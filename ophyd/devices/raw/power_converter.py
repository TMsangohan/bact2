from ophyd import EpicsSignal, EpicsSignalRO, PVPositionerPC, Component as Cpt
from ophyd.status import  SubscriptionStatus

# from ..utils import signal_with_validation
# from ..utils.ReachedSetPoint import ReachedSetpoint

class PowerConverter( PVPositionerPC ):
    """A power converter abstraction

    Currently only a device checking that the set and read value corresponds

    Todo:
        Insist on an hyseteres is loop
        Proper accuracy settings
    """
    setpoint = Cpt(EpicsSignal,   ':set')
    readback = Cpt(EpicsSignalRO, ':rdbk')
