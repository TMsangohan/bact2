"""Beam position monitor data

A higher level of access is provided by
:mod:`bact2.ophyd.bact2.ophyd.devices.pp.bpm`
"""
from ophyd import Component as Cpt, EpicsSignalRO
from ophyd import Device

from bact2.ophyd.devices.pp.VectorSignalRO import VectorSignalRO
from bact2.ophyd.devices.utils.EnsureNewValueWhenTriggered import EnsureNewValueWhenTriggered

class BPMStatistics( Device ):
    """Average statistics of the beam position monitor

    All BPM's are read by an IOC. Average data are provided by this IOC. These
    can be accessed by the signal provided in this class.
    """
    mean_x = Cpt(EpicsSignalRO, ":avgV")
    mean_y = Cpt(EpicsSignalRO, ":avgH")
    rms_x  = Cpt(EpicsSignalRO, ":rmsV")
    rms_y  = Cpt(EpicsSignalRO, ":rmsH")

class BPMPackedData( Device ):
    """Common readings of all Beam position monitor data

    This class provides access to the data as received by the IOC.
    A higher level of access is provided by
    :class:`bact2.ophyd.bact2.ophyd.devices.pp.bpm.BPMWaveform`
    Ensures that always a new value will be read
    """
    #: packed data containing different values
    packed_data = Cpt(VectorSignalRO , ":bdata")
    #: counter: the last reading?
    counter  = Cpt(EpicsSignalRO,   ":count")
    #: data ready to take?
    ready    = Cpt(EpicsSignalRO,  ":ready")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_trigger = EnsureNewValueWhenTriggered(minimum_delay = 10e-3, timeout = 3.0)

    def trigger(self):
        return self.new_trigger.trigger_check(self.packed_data)
