import time

from bact2.ophyd.utils.status.ExpectedValueStatus import ExpectedValueStatus

class EnsureNewValueWhenTriggered:
    """
    Make sure a new value is returned when triggered

    Saves the timestamp of the last trigger. Will only accept a
    value if its timestamp is larger than the
    stored one + the minimum delay

    Furthermore the method :meth:`set_done` can be used to set the
    timestamp to the current (unix) clock time. This method can be
    used to ensure that the trigger will only accept data which
    has been received after this new timestamp. One use cas is to
    register set_done with :meth:`ophyd.status.Status.finished_cb`,
    so that it will be called after a device has successfully
    reached its new setting.
    """
    def __init__(self, minimum_delay = 0.0, timeout = None):
        self._last_timestamp = None
        self.minimum_delay = minimum_delay
        self._count = 0
        self._timeout = timeout

    @property
    def minimum_delay(self):
        return self._minimum_delay

    @minimum_delay.setter
    def minimum_delay(self, delay):
        delay = float(delay)
        assert(delay >= 0)
        self._minimum_delay = delay

    def set_done(self):
        """
        Inform that status has changed

        Update the internal timestamp to the this one. Thus old data will
        not be accepted.
        """
        now  = time.time()

        if ( self._last_timestamp is None ) or ( self._last_timestamp < now ):
            self._last_timestamp = now

    def trigger_check(self, var):
        """
        Ensure that new data was received.

        Based on :class:`SubscriptionStatus`
        """

        def callback(*args, **kwargs):
            timestamp = kwargs["timestamp"]
            if self._last_timestamp is None:
                self._last_timestamp = timestamp

            dt = timestamp - self._last_timestamp
            if self._count > 0:
                print("cnt {} dt {}".format(self._count, dt))
            self._count += 1

            if dt > self.minimum_delay:
                self._last_timestamp = timestamp
                return True
            else:
                return False

        self._count = 0

        kws = {"run" : False,
                   }

        if self._timeout is not None:
            kws["timeout"] = self._timeout

        status = ExpectedValueStatus(var, callback, **kws)
        
        return status
