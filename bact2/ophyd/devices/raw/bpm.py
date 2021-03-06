"""Beam position monitor data

A higher level of access is provided by
:mod:`bact2.ophyd.bact2.ophyd.devices.pp.bpm`
"""
from ophyd import Component as Cpt, EpicsSignalRO
from ophyd import Device
from ophyd.status import SubscriptionStatus, AndStatus
from ...utils.status.ExpectedValueStatus import ExpectedValueStatus

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

    Check of bpm state and data reading is done in
    :class:`BPMMeasurementStates`
    """
    #: packed data containing different values
    packed_data = Cpt(EpicsSignalRO , ":bdata")
    #: counter: the last reading?
    counter  = Cpt(EpicsSignalRO,   ":count")
    #: data ready to take?
    ready    = Cpt(EpicsSignalRO,  ":ready")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # from .bpm_state_engine import BPMMeasurementStates
        # self.measurement_state = BPMMeasurementStates(parent = self)
        self.bpm_timeout = 3.0
        self.validation_time = 0.1

    def trigger(self):
        """Inform the measurement state engine that measurement starts


        ensure that ready falls off. Only then accept packed data

        Todo:
            Check if assumptions are correct...
        """
        # Inform the measurement state engine that data acquistion
        # starts


        ready_negative_edge_triggered = False
        def trigger_falling(value = None, old_value = None, **kwargs):
            '''waiting for falling edge trigger of ready
            '''
            nonlocal ready_negative_edge_triggered

            old_value = bool(old_value)
            value = bool(value)

            if old_value and not value:
                ready_negative_edge_triggered = True
                return True
            return False


        def cb(**kwargs):
            """Wait for new data

            If this data is here we are done ...

            All this nice checks do not work
            """
            return True

            nonlocal ready_negative_edge_triggered
            if ready_negative_edge_triggered:
                return True
            return False

        # ready_stat = SubscriptionStatus(self.ready, trigger_falling, timeout = self.bpm_timeout, run = False)
        stat_pkd   = SubscriptionStatus(self.packed_data, cb, timeout = self.bpm_timeout * 2, run = False)
        # status = AndStatus(ready_stat, stat_pkd)
        return stat_pkd

        #status = self.measurement_state.watch_and_take_data(timeout = self.bpm_timeout,
        #                                                        validation_time = self.validation_time)
        #return status

    def read(self, *args, **kwargs):
        """reads the data and resets state engine
        """
        r = super().read(*args, **kwargs)
        # self.measurement_state.set_idle()
        return r
