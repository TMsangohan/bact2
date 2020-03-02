from ..utils import measurement_state_machine
from ...utils import execute_async
from ophyd.status import DeviceStatus
import time
import logging
import functools

logger = logging.getLogger("bact2")


class BPMMeasurementStates:
    """Follow the state of the BPM readings

    User is expected to:
        * define signal variables in a :class:`ophyd.Device`
          for the variables

            * packed data
            * counter
            * ready

        * call :meth:`watch_and_take_data` when the data
          should be acuired. This is typically called when
          data taking is triggered by the Device

        * call :meth:`set_idle` when the data have been transfered
          This is typically called by

        * to call  :meth:`set_triggered` to inform that the state
           data acquistion supervision shall satart. This is
           typically called by :meth:`bpm.trigger`

        *  :meth:`set_idle` to inform that the acquired measurement
           have been taken. This is typically called by
           :meth:`bpm.read`

    measurement states are defined in
    :class:`measurement_state_machine.AcquisitionState`

    The BPM's IOC sometimes sends packed data a little to early.
    On the other hand it exports its internal update counter and
    a ready flag. Therefore this class is used to:

        * check the value of the ready flag
        * check the counter change

    When the state machine is triggered, it will switch to
    acquisition mode as soon as the :any:`ready` flags is found low.
    Then the state machine is set to acquire. As soon as ready is
    turning from low to high the state engine is set to valudate.

    In the validate regime it is checking if new data is still
    arriving. If new data arrives, it will wait again for
    the *validation time* time span to see if new data arrives.
    As soon as no new data arrives during this time span, it will
    set its state to finished and call _finished on the device
    object.
    """
    def __init__(self, *args, parent = None, **kwargs):
        assert(parent is not None)
        self.__timestamp = None
        self._counter = None
        self.parent = parent
        self.createMethodsDic()
        self.measurement_state = measurement_state_machine.AcquisitionState()
        self._execute_async = execute_async.ExecuteAsynchronisly()
        self.__logger = logger

    def setLogger(self, logger):
        self.__logger = logger

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
        self.__timestamp = time.time()

    @property
    def dt(self):
        """Time since triggered

        Used for logging as user information
        """
        if self.__timestamp is None:
            return -1.0

        now = time.time()
        dt = now - self.__timestamp
        return dt

    def checkCounter(self, val):
        val = int(val)
        if self._counter is None:
            self._counter = val
            return


        if val == self._counter:
            fmt = "At {:.3f} got same counter value {} once again"
            self.__logger.debug(fmt.format(self.dt, self._counter))
            return None

        state = self.measurement_state
        fmt = "At {:.5f} state {} counter value changed from {} to {} "
        txt = fmt.format(self.dt, state.state, self._counter, val, )


        if state.is_idle:
            self.__logger.info(txt)
            return None

        elif state.is_triggered:
            self.__logger.info(txt)
            self._counter = None
            return None

        elif state.is_acquire:
            self.__logger.info(txt)
            return txt

        elif state.is_validate:
            self.__logger.info(txt)
            return txt

        elif state.is_finished:
            self.__logger.error(txt)
            raise AssertionError(txt)

        elif state.is_failed:
            self.__logger.info(txt)
            return txt
        else:
            raise AssertionError("should not end up here")

    def set_idle(self):
        """Typically: we are done ..
        """
        self.measurement_state.set_idle()
        # self._timestamp = None
        self._counter = None

    def set_triggered(self):
        """

        Todo:
            Review if the subscription should be permanent?
        """
        self.measurement_state.set_triggered()
        self._counter = None
        self.tic()
        self.__logger.info("At {:.3f} s: triggered acquisition ".format(self.dt))

    def set_acquire(self):
        """

        When BPM signals that status is finished set the state
        engine to finished to
        """
        fmt = "At {:.3f} s: setting to acquire mode after "
        self.__logger.info(fmt.format(self.dt))
        self.measurement_state.set_acquire()

    def set_validate(self):
        fmt = "At {:.3f} s: setting to validate mode"
        self.__logger.info(fmt.format(self.dt))
        self.measurement_state.set_validate()
        self.tic()

    def set_finished(self):
        """

        Remove the callbacks to the changed values
        """
        self.__logger.info("At {:.3f} s: finished acquistion ".format(self.dt))
        self.measurement_state.set_finished()

    def set_failed(self):
        self.__logger.warning("Switched to fail state dt = {:.3f}".format(self.dt))
        self.measurement_state.set_failed()

    def onValueChange(self, *args, obj = None, **kwargs):
        """Common dispatch method for the triggers

        This method is subscribed to all bpm variables when
        set_trigger is called. This method is then unsbuscribed when
        set_finish is called.


        The value change is then dispatched to the method for the differeent
        states.

        Todo:
            Check if subscribtion to the variable is not best handled by
            a proper wrapper
        """

        raw_name = kwargs.pop('name', None)
        if obj is not None:
            raw_name = obj.name

        # Now lets find the name of the variable from the concatenated string
        translations = {
            'bpm_waveform_ready'       : 'ready',
            'bpm_waveform_counter'     : 'counter',
            'bpm_waveform_packed_data' : 'packed_data'
        }
        try:
            name = translations[raw_name]
        except KeyError as ke:
            name = raw_name
        # All methods expect a translated name
        kwargs.setdefault('name', name)

        method = self.onValueChangeMethods[self.measurement_state.state]

        fmt = "At {}:,3f onValueChange delegating to {} args {} kwargs {}"
        self.__logger.debug(fmt.format(self.dt, method, args, kwargs))

        r = method(*args, **kwargs)
        return r

    def onValueChangeIdle(self, *args, name = None, **kwargs):
        """

        Todo:
            Review if exception to be raised if called
        """
        self.__logger.info("on value idle args {} kwargs {}".format(args, kwargs))

        fmt = "Idle: should not have been called: dt {} name {}"
        self.set_failed()
        raise AssertionError(fmt.format(dt, name))


    def onValueChangeTriggered(self, *args, name = None, **kwargs):
        """Start acquiring when ready signals low value

        Todo:
           Check if ready == 0 means that acquisition started
        """
        #self.log("on value triggered args {} kwargs {}".format(args, kwargs))

        self.__logger.info("At {:.3f} s: change triggered by name {}".format(self.dt, name))
        if name == "ready":
            ready = kwargs["value"]
            txt = "At {:.3f} s: triggered ready val = {}".format(self.dt, ready)
            self.__logger.info(txt)
            if not ready:
                # Waiting for the data!
                self.set_acquire()

    def onValueChangeAcquire(self, *args, name = None, **kwargs):
        """Acquire data as long as ready is low

        If ready returns to high switch to validate
        """
        #self.log("on value acquire args {} kwargs {}".format(args, kwargs))
        self.__logger.debug("At {:.3f} s: on change acquire name {}".format(self.dt, name))

        value = kwargs["value"]
        if name == 'ready':
            ready = value
            self.__logger.info("At {:.3f} s: acquire ready val = {}".format(self.dt, ready))
            if ready:
                self.set_validate()

        elif name == 'counter':
            txt = self.checkCounter(value)
            if txt:
                self.__logger.info(txt)
                self.set_validate()

        elif name == 'packed_data':
            self.set_validate()

        else:
            self.set_failed()
            raise AssertionError("name {} unknown".format(name))

    def onValueChangeValidate(self, *args, name = None, **kwargs):
        """Accept the last packed data arriving during validation time

        Assumes that packed_data are sent out after ready goes back
        to high

        Todo:
            Review if a check should be made if ready falls off to low
        """
        # self.log("on value validate args {} kwargs {}".format(args, kwargs))
        self.__logger.info("At {:.3f}: validate {}".format(self.dt, name))


        value = kwargs["value"]
        if name == "ready":
            ready = value
            self.__logger.info("Validate dt {:.3f} ready val = {}".format(self.dt, ready))

        elif name == 'counter':
            self.checkCounter(value)

        elif name == 'packed_data':
            self.__logger.info("Validate got bdata: now last check")

        else:
            self.set_failed()
            raise AssertionError("name {} unknown".format(name))


    def onValueChangeFinished(self, *args, name = None, **kwargs):
        """
        Todo:
            Review if exception should be raised if called
        """
        self.__logger.info("on value finished args {} kwargs {}".format(args, kwargs))
        fmt = "Finished: should not have been called: dt {} name {}"
        self.set_failed()
        raise AssertionError(fmt.format(dt, name))

    def onValueChangeFailed(self, *args, name = None,  **kwargs):
        """

        Todo:
            Review if exception should be raised if called
        """
        self.__logger.info("on value failed args {} kwargs {}".format(args, kwargs))
        fmt = "Failed: should not have been called: dt {} name {}"
        raise AssertionError(fmt.format(dt, name))


    def watch_and_take_data(self, timeout = None, validation_time = None):
        """Get the bpm data at the right moment

        This method does the heavy lifting. Installs callbacks for data
        updates

        Args:
            timeout : mamimum time the data taking shall take
            validation time : how long to wait that no new data have
            arrived

        Returns : :class:`ophyd.status.DeviceStatus` object


        Todo:
            Finish documentation
        """
        timeout = float(timeout)
        validation_time = float(validation_time)

        if timeout < 0.0:
            raise AssertionError("timeout {} < 0".format(timeout))

        if validation_time < 0.0:
            raise AssertionError("validation time{} < 0".format(validation_time))

        if validation_time > timeout:
            fmt = "validation time {} must not be larger than timeout {}"
            raise AssertionError(fmt.format(validation_time, timeout))

        # Why do I need to do that here ..
        # self.tic()


        status = DeviceStatus(self.parent, timeout = timeout)
        # Does this raise an exception on failure?
        self.set_triggered()
        if self.measurement_state.is_failed:
            status._finished(success = False)
            return status


        signals = self.parent.ready, self.parent.counter, self.parent.packed_data
        def clear_callbacks_to_signals():
            """Clear the update_cb to the signals

            Required at different locations. Thus declared here
            """
            nonlocal signals
            for signal in signals:
                signal.clear_sub(update_cb)

        # Used as a counting semaphore ... it is incremented in
        # update_cb if in validation state
        n_updates_during_validation = 0
        def check_and_finish(ref_cnt):
            """Finish if no new data has arrived while validation
            Checks the counter value if it matches the refcount
            """
            nonlocal n_updates_during_validation, status

            if n_updates_during_validation != ref_cnt:
                fmt = "At {:.3f} s: validating: expected {} validation calls but found {} calls."\
                  " Not setting finish"
                self.__logger.warning(fmt.format(self.dt, ref_cnt, n_updates_during_validation))
                return

            fmt = "At {:.3f} s: finishing at {} validation calls"
            txt = fmt.format(self.dt, ref_cnt)
            if ref_cnt > 1:
                self.__logger.warning(txt)
            # That's necessary. Not known if this callback will end up here again
            clear_callbacks_to_signals()
            self.set_finished()
            status._finished()


        def update_cb(*args, **kwargs):
            """Common callback to the signals

            Hands the data over self.onValueChangeg to trace the change.
            Set the status depending on the state machine status
            Handles validation over to :func:`check_and_finish`
            """
            nonlocal status, signals, n_updates_during_validation

            if status.done:
                clear_callbacks_to_signals()

            try:
                self.onValueChange(*args, **kwargs)
            except Exception as e:
                clear_callbacks_to_signals()
                fmt = "onValueChange failed for args {} kwargs {} reason: {}"
                self.__logger.error(fmt.format(args, kwargs, e))
                status._finished(success = False)
                raise e
                return

            if self.measurement_state.is_finished:
                clear_callbacks_to_signals()
                status._finished(success = True)
                return

            elif self.measurement_state.is_failed:
                clear_callbacks_to_signals()
                status._finished(success = False)
                return

            elif self.measurement_state.is_validate:
                # Check if a signal was still called
                # The details are handled by :func:`check_and_finish`
                # NB: n_updates_during_validation must be an in place increment
                n_updates_during_validation += 1
                f = functools.partial(check_and_finish, n_updates_during_validation)
                self._execute_async.callLater(validation_time, f)

            else:
                pass

        # Everything defined over the call backs. So let's
        # subscribe them and let the call backs do the work
        for signal in signals:
            signal.subscribe(update_cb, run = False)

        return status
