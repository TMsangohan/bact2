import asyncio
import threading
import time 
import datetime

class ExecuteAsynchronisly:
    """Execute function later or at a given time

    Uses asyncio if the event loop is running. If it is not
    running execute threading.Thread

    Todo:
        This code is a copy of bluesky examples. It should be
        checked if if it would be sufficient to just use
        :func:`asynio.call_later`
    """
    def __init__(self):
        self.loop = asyncio.get_event_loop()

    def callLater(self, delay, func):
        """Call func after at minimum delay has expired

        Args:
            delay : delay to wait in seconds
            func : function to evaluate
        """
        if self.loop.is_running():
            self.loop.call_later(delay, func)

        else:
            def sleep_and_finish():
                nonlocal func
                time.sleep(delay)
                func()

            threading.Thread(target=sleep_and_finish, daemon=True).start()

    def callAt(self, timestamp, func):
        """Call a function not earler than the given time stamp

        This function should handle it over to a system function and not 
        the other way round ....


        Todo:
            What to do if the request timestamp has already passed?
        """
        raise NotImplementedError("Code below is not yet checked")
        now = time.time()
        delay = now - timestamp

        if delay < 0:
            fmt = "Time of execution {} (timestamp {}) already passed as now is {} (timestamp {})"
            d_ts, d_now = [datetime.datetime.fromtimestamp(t) for t in (timestamp, now)]
            raise AssertionError(fmt.fomat(timestamp, d_ts, now, d_now))

        self.callLater(delay, func)