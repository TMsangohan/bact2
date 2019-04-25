import numpy as np
from ophyd import Component as Cpt, Device, PVPositionerPC, PVPositioner
from ophyd import EpicsSignal, EpicsSignalRO

from ..utils import ReachedSetPoint


class MasterClockFrequency(ReachedSetPoint.ReachedSetpoint):
    """Access to frequency of the master clock

    __init__ requires to set setting_parameters.

    Check :class:`device_utils.ReachedSetpoint` for details
    """
    setpoint = Cpt(EpicsSignal,   'MCLKHX251C:freq')
    readback = Cpt(EpicsSignalRO, 'MCLKHX251C:hwRdFreq')

class MasterClock(Device):
    """BESSY II Master clock

    Warning:
        Critically review the frequency range

    Todo:
        Make the code more generic so that it could be used for
        other master clocks
    """
    _ref_freq = 499630
    _df_max = 4
    frequency = Cpt(MasterClockFrequency, # name = 'MCLKHX251C',
                    egu='kHz', limits = (_ref_freq - _df_max, _ref_freq + _df_max),
                    #settle_time = 5.0
                    #setting_parameters = 1.0
                    setting_parameters = 0.1
    )
    #frequency.done_value = 1


