from ....math.root_finder import LinearGradient as LG, CautiousRootFinder as CR
from ophyd import Component as Cpt, Device, Signal, Kind
import numpy as np

import threading
import queue

class LinearGradient(Device):
    '''Encapsulation for LinearGradient
    '''
    scale_gradient = Cpt(Signal, name='scale_gradient', value=1.0, kind=Kind.config)
    start_gradient = Cpt(Signal, name='start_gradient', value=1.0, kind=Kind.config)

    x_vals = Cpt(Signal, name='x_vals', value=[], kind=Kind.normal)
    f_vals = Cpt(Signal, name='f_vals', value=[], kind=Kind.normal)
    df = Cpt(Signal, name='df', value=np.nan, kind=Kind.normal)

    def __init__(self, *args, func=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._obj = None
        self._func = None
        if func is not None:
            self.setFunc(func)

    def setFunc(self, func):
        self._func = func

    def reset(self):
        self._obj = None
        self.x_vals.value = []
        self.f_vals.value = []
        self.df.value = np.nan

    def init(self):
        if not callable(self._func):
            raise AssertionError(f'func {self._func} is not callable')
        self._obj = LG(func=self._func,
                       scale_gradient=self.scale_gradient.value,
                       start_gradient=self.start_gradient.value,
        )

    def eval(self, x):
        # Better error message here
        assert(self._obj is not None)
        f, df = self._obj(x)
        self.x_vals.value = self._obj.x()
        self.f_vals.value = self._obj.f()
        self.df.value = df
        return f, df

class CautiousRootFinder(Device):
    xtol = Cpt(Signal, name='xtol', value=.1, kind=Kind.config)
    ytol = Cpt(Signal, name='ytol', value=.1, kind=Kind.config)
    x0   = Cpt(Signal, name='x0',   value=0.0, kind=Kind.normal)
    extp = Cpt(Signal, name='extrapolated', value=True, kind=Kind.normal)

    lg = Cpt(LinearGradient, name='lg')

    def __init__(self, *args, func=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._obj = None
        self._thread = None
        if func is not None:
            self.setFunc(func)
        self._vals = []

        self.q_setp = queue.Queue(maxsize=1)
        self.q_rdbk = queue.Queue(maxsize=1)
        self.queue_get_timeout = 30
        self.queue_put_timeout = .1
        self.result = None

    def setFunc(self):
        def wrapper(x):
            self.q_setp.put(x, timeout=self.queue_put_timeout)
            r = self.q_rdbk.get(timeout=self.queue_get_timeout)
            self.log.info(f'For x {x} returning to root solver {r}')
            return r

        self.lg.setFunc(wrapper)

    def reset(self):
        self.lg.reset()
        self._obj = None
        self.extp.value=True

    def init(self):
        self.setFunc()
        self.lg.init()
        self._obj = CR(func=self.lg._obj, x0=self.x0.value)

    def push(self, r):
        self.log.info(f'Result returned {r} ')
        self.q_rdbk.put(r, timeout=self.queue_put_timeout)


    def __iter__(self):
        self.reset()
        self.init()

        the_root = None

        def thread_func():
            nonlocal the_root
            r = self._obj.find_root()
            # Signal ... that's all folks
            self.log.info(f'Result converged to {r}')
            self.q_setp.put(None, timeout=self.queue_put_timeout)
            the_root = r
            return

        thread = threading.Thread(target=thread_func)
        thread.start()
        self._thread = thread

        while True:
            x = self.q_setp.get(timeout=self.queue_get_timeout)
            self.log.info(f'Next step {x} ')
            if x is None:
                # Signal ... that's all folks
                # self._thread.join(timeout=self.queue_put_timeout)
                # del self._thread
                self.result = the_root
                return the_root
            yield x
