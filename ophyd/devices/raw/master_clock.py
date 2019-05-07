"""

@author: Pierre Schnizer, Markus Ries
"""

import numpy as np
from ophyd import Component as Cpt, Device
from ophyd import EpicsSignal, EpicsSignalRO

from ..utils.ReachedSetPoint import ReachedSetpoint


class ReachedSetpointWithOffsetCorrection( ReachedSetpoint ):
    """Correct master clock read back for orbit corrections
    """
    def _correctReadback(self, val):
        offset = self.offset.get()
        val = val - offset
        return val


class MasterClockFrequency( ReachedSetpointWithOffsetCorrection ):
    """Access to frequency of the master clock


    The master clock frequency is tightly coupled to the real orbit length.
    For the ideal undisturbed orbit of BESSY II this corresponds to the
    frequency of :math:`\approx\,499626\, kHz`


    If orbit bumps are added or strong insertion devices are activated, the
    total orbit length is changed. This change is reflected as feed forward
    in an offset variable.

    The setpoint is given as a value. Then the offset is added and then set
    to the hardware clock. Only this value can be read back. Therefore the
    offset must be deduced from the read back so that the setpoint and
    readback can match.


    __init__ requires to set setting_parameters.

    Check :class:`device_utils.ReachedSetpoint` for details of the init
    keywords.
    """
    setpoint = Cpt(EpicsSignal,   'MCLKHX251C:freq')
    readback = Cpt(EpicsSignalRO, 'MCLKHX251C:hwRdFreq')

    #: Offset tries to compensate the lengthing of the machine
    offset   = Cpt(EpicsSignalRO, 'MCLKHX251C:sum_off')

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
                    setting_parameters = 0.1,
                    timeout = 2
    )
    #frequency.done_value = 1


