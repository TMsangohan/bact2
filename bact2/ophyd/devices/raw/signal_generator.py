"""Collection of signal generators

Currently only the noise generator has been implemented
"""

from ophyd import Device, EpicsSignal, EpicsSignalRO, PVPositionerPC
from ophyd import Component as Cpt
from ..utils.ReachedSetPoint import ReachedSetpoint

class NoiseGeneratorChannel(ReachedSetpoint):
    """Noise generator channel ... has two different signals

    The noise generator device can be seen like a motor:
        * change the noise level
        * check that the level has been reached (settle time)
        * ready to sample

    Todo:
        Check that the output is enabled and active. Possibly best during the
        :mod:`stage`

    """
    setpoint = Cpt(EpicsSignal,   ':setVolt')
    readback = Cpt(EpicsSignalRO, ':rdVolt')
    output   = Cpt(EpicsSignal,   ':cmdOut')
    output_enabled = Cpt(EpicsSignalRO, ':stOut')

class NoiseGenerator(Device):
    """BESSY II Noise generator
    """
    x = Cpt(NoiseGeneratorChannel, 'WFGENC2S7G', egu='V', limits = (0, 5), settle_time = 1.0,
            timeout = 1.0,  setting_parameters = .1)
    y = Cpt(NoiseGeneratorChannel, 'WFGENC1S7G', egu='V', limits = (0, 5), settle_time = 1.0,
            timeout = 1.0,  setting_parameters = .1)
