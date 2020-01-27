import threading
import queue
import asyncio

import time
import sys
import functools

from ophyd.status import DeviceStatus, SubscriptionStatus
from bact2.ophyd.utils.status.ExpectedValueStatus import ExpectedValueStatus

import logging

logger = logging.getLogger()

class FlickerSignal:
    """Returns data, if no further data is provided during validation time

    Some IOC's send data and resend data after a short while
    because extra has been received. This class allows handling
    such issues.

    Warning:
        Not tested code

    Implementation:
       * when triggered a call back is subscribed to the variable
       * this callback increments the instance variable n_triggered
       * then a delay is entered (as separate thread or using
         asyncio)
       * after the delay the value n_triggered is checked
       * if it is still the same the status object is marked as done
       * if n_triggered has increased, it is assumed that an other
         call is running and will eventually mark the status object
         as done
    """
    def __init__(self, signal, timeout = 3, validation_time = .1):
        """

        Args:
            signal : an :class:`ophyd.Signal` signal instance to
                     watch
        """
        self.signal = signal

        # Time until the first reading has to arrive!
        self.timeout = timeout # s

        # Time to wait that new data arrives
        self.validation_time = validation_time #s
        self.loop = asyncio.get_event_loop()
        # Used to find if data was resent
        self._n_triggered = 0

        # Set the info on timing
        self.tic()
        self.tac()

    def tic(self):
        self._t0 = time.time()

    def dt(self):
        now = time.time()
        dt = now - self._t0
        return dt

    def tac(self):
        self._store_dt = self.dt()

    def stored_dt(self):
        return self._store_dt

    def setLogger(self, logger):
        self.log = logger

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, val):
        val = float(val)
        assert(val >=0)
        self._timeout = val

    @property
    def validation_time(self):
        return self._validation_time

    @validation_time.setter
    def validation_time(self, val):
        val = float(val)
        assert(val >= 0)
        self._validation_time = val

    def check_if_new_reading(self, expected_count, book_keeping = None):
        """Just allow for it to arrive!
        """

        # device_status = self._device_status
        device_status = book_keeping.device_status
        assert(device_status is not None)
        now_count =  self._n_triggered
        fmt = "New data arrived?  counts: expected {} found {} "
        self.log.info(fmt.format(expected_count, now_count))
        if now_count == expected_count:
            self.log.debug("No new data arrived: done cnt {} unscribing!".format(now_count))
            assert(self.signal is not None)
            self.log.debug("No new data arrived: marking device_status {} id({}) as done !".format(device_status, id(device_status)))
            # print("Unwrapped callbacks {} wrapped callbacks {}".format(
            #    self.signal._unwrapped_callbacks,
            #    self.signal._callbacks
            #    ))
            device_status._finished(success = True)
            # cid = book_keeping.cid
            # assert(cid is not None)
            # self.signal.unsubscribe(cid)
            self._device_status = None
            del device_status

        else:
            self.tac()
            fmt = "New data arrived after {}: Expecting other trigger to mark status as done"
            self.log.debug(fmt.format(self.stored_dt()))

    def delay_signal_status(self, *args, book_keeping = None, **kwargs):
        """
        """
        def log_debug(txt):
            tref = time.time() - self._t0
            txt = "tref {:.2f} ".format(tref) + txt
            self.log.debug(txt)


        assert(book_keeping is not None)

        self._n_triggered += 1
        ref_cnt = self._n_triggered
        log_debug("Handling reading {}".format(ref_cnt))

        def check_and_finish():
            nonlocal ref_cnt, book_keeping
            self.check_if_new_reading(ref_cnt, book_keeping = book_keeping)

        if self.loop.is_running():
            #log_debug("Executing using asyncio loop")
            self.loop.call_later(self.validation_time, check_and_finish)

        else:
            #log_debug("Executing using thread")
            def sleep_and_finish():
                time.sleep(self.validation_time)
                check_and_finish()

            threading.Thread(target=sleep_and_finish, daemon=True).start()

        log_debug("Finished delay signal status")
        return True

    def execute_validation(self, device_status, run = True):
        """

        Warning:
            Don"t forget to unsubscribe again!
        """
        assert(device_status is not None)

        self._n_triggered = 0
        self.tic()

        class callback:
            def __init__(self, parent = None, device_status = None):
                self.parent = parent
                self.device_status = device_status
                self.cid = None

            def __call__(self, *args, **kwargs):
                self.parent.delay_signal_status(*args, book_keeping = self, **kwargs)

        book_keeping = callback(parent = self, device_status = device_status)

        def cb(*args, **kwargs):
            nonlocal book_keeping
            self.delay_signal_status(*args, book_keeping = book_keeping, **kwargs)

        def unsubscribe():
            nonlocal cb
            self.signal.clear_sub(cb)

        device_status.add_callback(unsubscribe)
        self.signal.subscribe(cb,  run = run)

        # print("Subscribers {}".format(self.signal._unwrapped_callbacks))

    def trigger_and_validate(self):
        #print("Got trigger: state machine state {}".format(self._acquisition_state.state))
        kws = {"run" : False}
        if self._timeout is not None:
            kws["timeout"] = self._timeout

        assert(self.signal is not None)
        device_status = DeviceStatus(device=self.signal, timeout=self.timeout)
        self.execute_validation(device_status, run=False)
        return device_status

    def data_read(self):
        #print("Data read for {}".format(self.signal.name))

        #t_state = self._acquisition_state.state
        #if not self._acquisition_state.is_finished:
        #    raise AssertionError("state machine in state {} which is not finished!".format(t_state))
        #self._acquisition_state.set_idle()
        pass

    def set_done(self):
        pass
