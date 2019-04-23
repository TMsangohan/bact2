from ophyd import Component as Cpt
from ophyd import Device

from bact2.ophyd.devices.pp.VectorSignalRO import VectorSignalRO
from bact2.ophyd.utils.preprocessors.EnsureNewValueWhenTriggered import EnsureNewValueWhenTriggered

class BPMWaveformDetector( Device ):
    """
    Ensures that always a new value will be read
    """
    bpm_waveform = Cpt(VectorSignalRO , "MDIZ2T5G:bdata" )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_trigger = EnsureNewValueWhenTriggered(minimum_delay = 10e-3, timeout = 3.0)

    def trigger(self):
        return self.new_trigger.trigger_check(self.bpm_waveform)
