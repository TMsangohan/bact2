"""Beam position monitor data

A higher level of access is provided by
:mod:`bact2.ophyd.bact2.ophyd.devices.pp.bpm`
"""
from ophyd import Component as Cpt, EpicsSignalRO
from ophyd import Device
from ophyd.status import Status

from ..pp.VectorSignalRO import VectorSignalRO
from ..utils.EnsureNewValueWhenTriggered import EnsureNewValueWhenTriggered

from ..utils import signal_with_validation
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
    packed_data = Cpt(EpicsSignalRO , ":bdata")
    #: counter: the last reading?
    counter  = Cpt(EpicsSignalRO,   ":count")
    #: data ready to take?
    ready    = Cpt(EpicsSignalRO,  ":ready")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_trigger = EnsureNewValueWhenTriggered(minimum_delay = 10e-3, timeout = 3.0)
        #self.validated_data = signal_with_validation.FlickerSignal(self.packed_data)

    def trigger(self):
        return self.new_trigger.trigger_check(self.packed_data)
        #return self.validated_data.trigger_and_validate()
 
    def read(self, *args, **kwargs):
        r = super().read(*args, **kwargs)
        #self.validated_data.data_read()
        return r