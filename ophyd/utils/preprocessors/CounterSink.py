from ophyd import sim

class CounterSink( sim.SynAxisNoHints ):
    """Sink for a connter

    Args:
        delay (default = 0) : how long to wait after a request was made

    See :class:`ophyd.sim.SynAxisNoHints` for a description of a full set
    of keywords.

    When receiving a set it will inform the object set on inform_set_done one
    the new status.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._inform_on_set_done = None

    @property
    def inform_set_done(self):
        return self._inform_on_set_done

    @inform_set_done.setter
    def inform_set_done(self, obj):
        """

        Todo:
            Check that the appropriate methods are callable
        """
        assert(callable(obj.set_done))
        self._inform_on_set_done = obj


    def set(self, *args, **kwargs):
        """

        Todo:
           should it be more permissive and allow an not
           registered inform_on_set_done object?
        """
        status = super().set(*args, **kwargs)

        if self._inform_on_set_done is None:
            return status

        cb = self._inform_on_set_done.set_done
        if status.done:
            cb()
        else:
            status.finished_cb(cb)

        return status
