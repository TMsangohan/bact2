from ophyd import Component as Cpt, EpicsSignalRO
from ophyd import Device

from bact2.ophyd.devices.pp.VectorSignalRO import VectorSignalRO
from bact2.ophyd.utils.preprocessors.EnsureNewValueWhenTriggered import EnsureNewValueWhenTriggered

class BPMDetectorStatistics( Device ):
    """

    Warning:
       Untested code! 
    """
    mean_x = Cpt(EpicsSignalRO, ":avgV")
    mean_y = Cpt(EpicsSignalRO, ":avgH")
    rms_x  = Cpt(EpicsSignalRO, ":rmsV")
    rms_y  = Cpt(EpicsSignalRO, ":rmsH")

class BPMWaveformDetector( Device ):
    """
    Ensures that always a new value will be read
    """
    waveform = Cpt(VectorSignalRO , ":bdata")
    #: counter: the last reading?
    counter  = Cpt(EpicsSignalRO,   ":count")
    #: data ready to take?
    ready    = Cpt(EpicsSignalRO,  ":ready")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_trigger = EnsureNewValueWhenTriggered(minimum_delay = 10e-3, timeout = 3.0)

    def trigger(self):
        return self.new_trigger.trigger_check(self.waveform)


class BPMStorageRing( Device ):
    stat = Cpt(BPMDetectorStatistics, "BPMZR", name = "stat", # egu = "mm"
    )
    waveform = Cpt(BPMWaveformDetector, "MDIZ2T5G", name = "wavefrom")

    def trigger(self, *args, **kwargs):
        r = self.waveform.trigger(*args, **kwargs)
        return r
