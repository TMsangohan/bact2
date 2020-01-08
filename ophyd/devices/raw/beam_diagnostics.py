from ophyd import Component as Cpt, Device, PVPositionerPC, PVPositioner
from ophyd import EpicsSignal, EpicsSignalRO, Signal
from ophyd.status import DeviceStatus, AndStatus, SubscriptionStatus

class AvalanchePhotoDiodeDetector(Device):
    '''
    '''
    mb_current = Cpt(EpicsSignalRO, 'FPATCC:APD:MBcurrent')
    mb_current_raw = Cpt(EpicsSignalRO, 'FPATCC:APD:MBcurrentFull')
    timeout = Cpt(Signal, name='timeout', value=2)

    def trigger(self):
        # stat1 = super.trigger()
        # self.mb_integration_time.value

        timeout = self.timeout.value
        assert(timeout > 0)

        def cb(*args, **kwargs):
            return True

        stat1 = SubscriptionStatus(self.mb_current,     cb, timeout=timeout, run=False)
        stat2 = SubscriptionStatus(self.mb_current_raw, cb, timeout=timeout, run=False)
        status = AndStatus(stat1, stat2)
        return stat2
