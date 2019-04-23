import time
import threading 
from ophyd.status import  SubscriptionStatus

class ExpectedValueStatus( SubscriptionStatus ):
    """
    Use heuristic to report when next value is expected
    """
    def __init__(self, *args, **kwargs):
        """
        Let's see if something is required
        """
        super().__init__(*args, **kwargs)
        self._info_thread = None

        self.expected_total_time = 2.0

        if not self.done:
            # print("Subscribing to device {}".format(self.device.name))
            self.device.subscribe(self._notify_watchers,
                               # event_type=self.device.SUB_READBACK
                                      )

            thread = threading.Thread(target=self._inform_while_wait,
                                    daemon=True, name=self.device.name)
            self._info_thread = thread
            self._info_thread.start()

    def _settled(self,  *args, **kwargs):
        self.device.clear_sub(self._notify_watchers)
        self._watchers.clear()


    def _inform_while_wait(self):
        interval = .2
        n =  self.expected_total_time / interval
        n = int(n)
        # print("Informing on elapsed time {} times".format(n))
        for i in range(n):
            # print("Notifiying watchers {}".format(i))
            self._notify_watchers(None)
            time.sleep(interval)

    def _notify_watchers(self, value, *args, **kwargs):
        # *args and **kwargs catch extra inputs from pyepics, not needed here
        if not self._watchers:
            return

        now = time.time()
        ts  = self.device.timestamp
        time_elapsed = now - ts
        fraction = time_elapsed /  self.expected_total_time
        for watcher in self._watchers:
            # print("Notifying watcher {}".format(watcher))
            watcher(name=self.device.name,
                    current = time_elapsed,
                    initial = 0,
                    target  = self.expected_total_time,
                    unit= "s",
                    precision = 2,
                    time_elapsed=time_elapsed,
                    fraction=fraction)
