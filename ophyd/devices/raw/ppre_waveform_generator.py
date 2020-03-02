from ophyd import Component as Cpt, Device, EpicsSignalRO, EpicsSignal, PVPositionerPC

from ..utils import ReachedSetPoint

class PPREWaveformgeneratorFrequency( ReachedSetPoint.ReachedSetpoint ):
    setpoint = Cpt(EpicsSignal,   ":setFrq")
    readback = Cpt(EpicsSignalRO, ":rdFrq")

class PPREWaveformgenerator( Device ):
    freq = Cpt(PPREWaveformgeneratorFrequency, 'WFGENC1S10G', egu='Hz', settle_time = 1.0,
            timeout = 3.0,
            setting_parameters = .1
    )
