"""

Warning:
    Untested code!
"""
from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, Device, PVPositionerPC
from ..utils.ReachedSetPoint import ReachedSetpointEPS

base = ReachedSetpointEPS
base = PVPositionerPC

class InjectorDelay( base ):
    setpoint = Cpt(EpicsSignal,   'PAHB:sDelay')
    readback = Cpt(EpicsSignalRO, 'PAHB:pDelay')

class InjectorDelayLine( Device ):
    delay = Cpt(InjectorDelay,  egu='ns',
                    #setting_parameters = 5e-3, # ps accuracy
    )
