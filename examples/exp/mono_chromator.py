"""BESSY II Monochromator
"""
from ophyd import Device, Signal, EpicsSignal, EpicsSignalRO, PVPositioner, Component as Cpt
from ophyd.status import Status, AndStatus, SubscriptionStatus

class _Monochromator( PVPositioner ):
    setpoint    = Cpt(EpicsSignal,   ':monoSetEnergy')
    readback    = Cpt(EpicsSignalRO, ':monoGetEnergy')
    done        = Cpt(EpicsSignalRO, ':multiaxis:running')
    done_val = 0
    stop_signal = Cpt(EpicsSignal,   ':multiaxis:stop')
    stop_val = 1


    def trigger(self):
        """Trigger only after new data has arrived

        Deactivated not to interfere with :class:`PVPositioner`
        """
        return super().trigger()

        def cb_rdbk(**kwargs):
            self.log.warning("cb_rdbk got {}".format(kwargs))
            return True

        def cb_setp(**kwargs):
            self.log.warning("cb_setp got {}".format(kwargs))
            return True

        stat_rdbk = SubscriptionStatus(self.readback, cb_rdbk, run = False, timeout = 1, settle_time = 2)
        #stat_setp = SubscriptionStatus(self.setpoint, cb_setp, run = False, timeout = 1, settle_time = 2)

        #status = AndStatus(stat_rdbk, stat_setp)
        return stat_rdbk

class Monochromator( Device ):
    dev = Cpt(_Monochromator, 'u171dcm1', name = 'mc', egu = 'eV')
