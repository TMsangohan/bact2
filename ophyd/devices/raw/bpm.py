"""Beam position monitor data

A higher level of access is provided by
:mod:`bact2.ophyd.bact2.ophyd.devices.pp.bpm`
"""
from ophyd import Component as Cpt, EpicsSignalRO
from ophyd import Device
from ophyd.status import DeviceStatus, AndStatus

from ..pp.VectorSignalRO import VectorSignalRO
from .bpm_state_engine import BPMMeasurementStates
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
        self.validated_data = signal_with_validation.FlickerSignal(self.packed_data)
        # self.measurement_state = measurement_state_machine.AcquisitionState()
        self.measurement_state = BPMMeasurementStates(parent = self)
        self.bpm_status = None
        self.save_counter = None


    def trigger(self):
        #return self.new_trigger.trigger_check(self.packed_data)

        self.save_counter = None
        max_tries = 20

        bpm_timeout = 3.
        self.bpm_status = None
        self.bpm_status   = DeviceStatus(device=self.packed_data, timeout = bpm_timeout)
        self.measurement_state.set_triggered()

        # self.counter.subscribe()
        # self.ready.subscribe(self.measurement_state.onValueChange)
        # self.packed_data.subscribe(self.measurement_state.onValueChange)
        # bpm_status.add_callback(self.measurement_state.onValueChange)

        # print("bpm trigger finished")
        return self.bpm_status

    def read(self, *args, **kwargs):
        r = super().read(*args, **kwargs)
        self.validated_data.data_read()
        self.bpm_status = None
        self.measurement_state.set_idle()
        return r
