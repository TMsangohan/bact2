from bluesky import RunEngine
from bluesky.utils import ProgressBarManager, install_qt_kicker
from bluesky.callbacks.best_effort import BestEffortCallback

import bluesky.plans as bp
from ophyd.status import DeviceStatus
from ophyd.sim import SynAxis, det
import time as ttime
import threading


ref_t = ttime.time()

def step_delays(start_point, total_delay, start_value = 0, end_value = 1,
                interval = 0.2):
    
    last_t = start_point
    assert(total_delay > 0)
    end_t = total_delay + last_t

    while True:
        now = ttime.time()
        
        next_t = last_t + interval

        if next_t >= end_t:
            next_t = end_t
            
        to_wait = next_t - now
        to_wait_ms = to_wait * 1000

        
        #print(f'start {start_point - ref_t:.3f}'
        #      f'now  {now - ref_t:.3f}'
        #      f' end {end_t - ref_t:.3f}'
        #      f': delay {to_wait_ms:.3f} ms')

        last_t = next_t
        dt = now - start_point
        scale = dt/total_delay
        new_value = start_value * (1-scale) + end_value * scale
        
        if to_wait > 0:
            # Some time to wait
            #print(f"Required to wait {to_wait_ms} ms")
            yield to_wait, new_value
            continue
        
        elif to_wait <= 0:
            #print(f"Stop waiting {to_wait_ms} ms")
            # Should be finished already
            return
            
        else:
            print(f"Should never end here {to_wait_ms} ms!")
            raise AssertionError



class SimMoveStatus(DeviceStatus):
    def __init__(self, *args,
                 start_time = None, delay = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.done:
            dev = self.device
            dev.subscribe(self._notify_watchers,
                          event_type=dev.SUB_READBACK
            )            
            dev.readback.subscribe(self._notify_watchers,
                                   event_type=dev.readback.SUB_VALUE
            )
            print('Subscribed to devices')

        self.start_time = start_time
        self.delay = delay
            
    def _settled(self,  *args, **kwargs):
        print('Device settled')
        self.device.clear_sub(self._notify_watchers)
        self._watchers.clear()

    def _notify_watchers(self, value, *args, **kwargs):
        if not self._watchers:
            # print(f'No watchers installed: {self._watchers}')
            return
        
        dev = self.device

        current = dev.readback.value
        target = dev.setpoint.value
        
        now = ttime.time()
        dt = now - self.start_time
        fraction = dt/self.delay
        pf = fraction * 100
        
        for watcher in self._watchers:
            # print(f'Calling watcher {watcher}: {current:.3f} -> {target:.3f}: {pf:.3f} %')
            watcher(name = dev.name, current = current, target = target,
                    time_elapsed = dt,
                    fraction = fraction)

    def watch(self, func):
        r = super().watch(func)
        print(f'Func {func} subscribing for watching: Watchers {self._watchers}!')
        return r
    
class SlowSimulatedAxis(SynAxis):
    def set(self, value):
        old_setpoint = self.sim_state['setpoint']
        self.sim_state['setpoint'] = value
        setpoint_ts = ttime.time()
        self.sim_state['setpoint_ts'] = setpoint_ts
        self.setpoint._run_subs(sub_type=self.setpoint.SUB_VALUE,
                                old_value=old_setpoint,
                                value=self.sim_state['setpoint'],
                                timestamp=self.sim_state['setpoint_ts'])
        
        def update_state(new_value):
            old_readback = self.sim_state['readback']
            self.sim_state['readback'] = new_value
            self.sim_state['readback_ts'] = ttime.time()
            self.readback._run_subs(sub_type=self.readback.SUB_VALUE,
                                    old_value=old_readback,
                                    value=self.sim_state['readback'],
                                    timestamp=self.sim_state['readback_ts'])
            self._run_subs(sub_type=self.SUB_READBACK,
                           old_value=old_readback,
                           value=self.sim_state['readback'],
                           timestamp=self.sim_state['readback_ts'])

        if not self.delay:
            update_state(value)
            return NullStatus()

        
        st = SimMoveStatus(device=self, start_time = setpoint_ts, delay = self.delay)
        delays = step_delays(setpoint_ts, self.delay, old_setpoint, value)
            
        if self.loop.is_running():
            def update():
                nonlocal delays
                for delay, new_value in delays:                        
                    update_state(new_value)
                    self.loop.call_later(delay, update)
                else:
                    st._finished()                
            update()
        else:
            def sleep_and_update():
                nonlocal delays
                for delay, new_value in delays:                        
                    ttime.sleep(delay)                
                    update_state(new_value)
                else:
                    st._finished()

            threading.Thread(target=sleep_and_update, daemon=True).start()
        return st

        
motor = SlowSimulatedAxis(name = 'motor', delay = 2)


    
RE = RunEngine({})
RE.waiting_hook = ProgressBarManager()
RE.subscribe(BestEffortCallback())
install_qt_kicker()

#RE.log.setLevel('WARNING')
detectors = [det]
RE(bp.scan(detectors, motor, 0, 3, num=2))
