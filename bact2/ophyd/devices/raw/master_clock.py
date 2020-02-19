"""

@author: Pierre Schnizer, Markus Ries
"""

import numpy as np
from ophyd import Component as Cpt, Device
from ophyd import EpicsSignal, EpicsSignalRO, Signal

from ..utils.ReachedSetPoint import ReachedSetpointEPS


class ReachedSetpointWithOffsetCorrection(ReachedSetpointEPS):
    """Correct master clock read back for orbit corrections
    """
    def _correctReadback(self, val):
        offset = self.offset.get()
        val = val - offset
        return val


class MasterClockFrequency( ReachedSetpointWithOffsetCorrection ):
    r"""Access to frequency of the master clock


    The master clock frequency is tightly coupled to the real orbit length.
    For the ideal undisturbed orbit of BESSY II this corresponds to the
    frequency of :math:`\approx 499626  kHz`


    If orbit bumps are added or strong insertion devices are activated, the
    total orbit length is changed. This change is reflected as feed forward
    in an offset variable.

    The setpoint is given as a value. Then the offset is added and then set
    to the hardware clock. Only this value can be read back. Therefore the
    offset must be deduced from the read back so that the setpoint and
    readback can match.

    """
    setpoint = Cpt(EpicsSignal,   'MCLKHX251C:freq')
    readback = Cpt(EpicsSignalRO, 'MCLKHX251C:hwRdFreq')

    #: Offset tries to compensate the lengthing of the machine
    offset   = Cpt(EpicsSignalRO, 'MCLKHX251C:sum_off')

    def annotate_eps(self, d):
        egu = self.egu
        name = self.name

        for cpt_suffix in ['eps_abs', 'eps_rel']:
            entry = name + '_' + cpt_suffix
            d[entry]['units'] = self.egu
            d[entry]['units'] = self.egu
            d[entry]['precision'] = 5
            d[entry]['precision'] = 5
            d[entry]['upper_ctrl_limit'] = 100.0
            d[entry]['lower_ctrl_limit'] = 0.0
        return d

    def describe(self):
        r = super().describe()
        # Annotate eps_rel and eps_abs information
        # can not be done directly

        r = self.annotate_eps(r)
        return r


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
    frequency = Cpt(MasterClockFrequency, name='f', timeout=2, egu='kHz')
    # name = 'MCLKHX251C',
    # limits = (_ref_freq - _df_max, _ref_freq + _df_max),
    # settle_time = 5.0
    # setting_parameters = 1.0
    # frequency.done_value = 1
