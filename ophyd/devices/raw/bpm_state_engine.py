from ..utils import measurement_state_machine, signal_with_validation
import time


class BPMMeasurementStates:

    def __init__(self, *args, parent = None, **kwargs):
        #super().__init__(self, *args, **kwargs)
        assert(parent is not None)
        self._timestamp = None
        self._counter = None
        self.parent = parent
        self.createMethodsDic()
        self.measurement_state = measurement_state_machine.AcquisitionState()
        self.__logger = None

    def setLogger(self, logger):
        self.__logger = logger

    def log(self, *args, **kwargs):
        if self.__logger is not None:
            self.__logger.info(*args, **kwargs)
        else:
            print(*args, **kwargs)

    def createMethodsDic(self):
        self.onValueChangeMethods = {
            "idle"      : self.onValueChangeIdle,
            "triggered" : self.onValueChangeTriggered,
            "acquire"   : self.onValueChangeAcquire,
            "validate"  : self.onValueChangeValidate,
            "finished"  : self.onValueChangeFinished,
            "failed"    : self.onValueChangeFailed,
            }

    def tic(self):
        self._timestamp = time.time()

    @property
    def dt(self):
        if self._timestamp is None:
            return -1.0

        now = time.time()
        dt = now - self._timestamp
        return dt

    def checkCounter(self, val):
        val = int(val)
        if self._counter is None:
            self._counter = val
        else:
            if val == self._counter:
                fmt = "Got same counter value {} once again"
                self.log(fmt.format(self._counter))
            else:
                fmt = "Counter value changed from {} to {}"
                raise AssertionError(fmt.format(self._counter, val))

    def set_idle(self):
        self.measurement_state.set_idle()
        self._timestamp = None
        self._counter = None

    def set_triggered(self):
        """

        Todo:
            Review if the subscription should be permanent?
        """
        self._counter = None
        self.measurement_state.set_triggered()

        for signal in (self.parent.counter, self.parent.ready, self.parent.packed_data):
            signal.subscribe(self.onValueChange, run = True)

        self.tic()
        self.parent.validated_data.tic()


    def set_acquire(self):
        self.measurement_state.set_acquire()

        bpm_status = self.parent.bpm_status
        bpm_status.add_callback(self.set_finished)

    def set_finished(self):
        """
        """
        self.log("Finished acquistion dt = {:.2f}".format(self.dt))
        for signal in (self.parent.counter, self.parent.ready, self.parent.packed_data):
            signal.clear_sub(self.onValueChange)

        for signal in (self.parent.counter, self.parent.ready, self.parent.packed_data):
            #self.log("Finished acquisition {} callbacks {}".format(signal.name, signal._unwrapped_callbacks))
            pass

        self.measurement_state.set_finished()


    def onValueChange(self, *args, obj = None, **kwargs):

        method = self.onValueChangeMethods[self.measurement_state.state]
        name = None
        if obj is not None:
            name = obj.name
            kwargs.setdefault('name', name)
        r = method(*args, **kwargs)
        return r

    def onValueChangeIdle(self, *args, **kwargs):
        self.log("on value idle args {} kwargs {}".format(args, kwargs))

    def onValueChangeTriggered(self, *args, name = None, **kwargs):
        #self.log("on value triggered args {} kwargs {}".format(args, kwargs))

        self.log("Triggered by name {}".format(name))
        if name == "bpm_waveform_ready":
            ready = kwargs["value"]

            self.log("Triggered ready val = {}".format(ready))
            if not ready:
                # Waiting for the data!
                self.set_acquire()

    def onValueChangeAcquire(self, *args, name = None, **kwargs):
        #self.log("on value acquire args {} kwargs {}".format(args, kwargs))
        self.log("on value acquire dt {:.2f} name {}".format(self.dt, name))
        if name == "bpm_waveform_ready":
            ready = kwargs["value"]
            self.log("Acquire dt {:.2f} ready val = {}".format(self.dt, ready))
            if ready:
                self.measurement_state.set_validate()

        elif name == "bpm_waveform_counter":
            val = kwargs["value"]
            self.checkCounter(val)

        elif name == "bpm_waveform_packed_data":
            self.log("Acquire dt {:.2f} got bdata".format(self.dt))

        else:
            raise AssertionError("name {} unknown".format(name))

    def onValueChangeValidate(self, *args, name = None, **kwargs):
        # self.log("on value validate args {} kwargs {}".format(args, kwargs))
        self.log("on value validate dt {:.2f} name {}".format(self.dt, name))
        if name == "bpm_waveform_ready":
            ready = kwargs["value"]
            self.log("Validate dt {:.2f} ready val = {}".format(self.dt, ready))

        elif name == "bpm_waveform_counter":
            val = kwargs["value"]
            self.checkCounter(val)

        elif name == "bpm_waveform_packed_data":
            self.log("Validate got bdata: now last check")
            validated_data = self.parent.validated_data
            status = self.parent.bpm_status
            validated_data.execute_validation(status)
        else:
            raise AssertionError("name {} unknown".format(name))
        pass

    def onValueChangeFinished(self, *args, **kwargs):
        self.log("on value finished args {} kwargs {}".format(args, kwargs))
        pass

    def onValueChangeFailed(self, *args, **kwargs):
        self.log("on value failed args {} kwargs {}".format(args, kwargs))
        pass
