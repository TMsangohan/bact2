"""Beam position monitors

Currently much focused on the implementation in BESSY II
"""
from ophyd import Component as Cpt, Signal, Device
from ophyd.status import DeviceStatus, AndStatus

from ..raw import bpm as bpm_raw
from ..utils import process_vector

def unpack_and_validate_data(packed_data, n_valid_items = None):
    """Split the packed data up to a matrix of bpm waveforms

    Args :
        packed_data : the data as received by the BPM

    Returns :
        mat : a matrix with the  different signals as row vectors
    """
    mat1  = process_vector.unpack_vector_to_matrix(packed_data, n_vecs = 2)
    with_data = mat1[0,:]
    unused = mat1[1,:]
    process_vector.check_unset_elements(unused, n_valid_rows = n_valid_items, unset_elements_value = 0)
    del unused

    mat = process_vector.unpack_vector_to_matrix(with_data, n_vecs = 8)
    for col in mat:
        # Why does that currently not work ?
        # process_vector.check_unset_elements(col, n_valid_rows = self.n_valid_bpms, unset_elements_value = 0)
        pass
    return mat

class BPMWaveform(  bpm_raw.BPMPackedData ):
    """Measurement data for the beam position monitors

    Todo:
        Reference to the coordinate system
        Clarify status values
        Clarify why data are given for "non existant monitors"
    """

    #: Number of valid beam position monitors
    n_valid_bpms = 112


    #: Relative horizontal beam offset as measured by the beam position monitors
    pos_x       = Cpt(Signal,  name = "dx")
    #: Relative vertical beam offset as measured by the beam position monitors
    pos_y       = Cpt(Signal,  name = "dy")
    #:
    intensity_z = Cpt(Signal,  name = "z")
    intensity_s = Cpt(Signal,  name = "s")
    status      = Cpt(Signal,  name = "status")
    gain        = Cpt(Signal, name = "gain")
    rms_x       = Cpt(Signal, name = "gain")
    rms_y       = Cpt(Signal, name = "gain")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check its there and an int
        self.n_valid_bpms = int(self.n_valid_bpms)
        assert(self.n_valid_bpms > 0)

    def storeDataInWaveforms(self, mat):
        """Store row vectors to the appropriate signals

        Args:
            mat : a matrix of vectors containing the appropriate input data
        Todo:
            Analyse the status values !
        """
        stat = mat[4]

        self.pos_x.set(      mat[0])
        self.pos_y.set(      mat[1])
        self.intensity_z.set(mat[2])
        self.intensity_s.set(mat[3])
        self.status.set(         stat)
        self.gain.set(       mat[5])
        self.rms_x.set(      mat[6])
        self.rms_y.set(      mat[7])


    def checkAndStorePackedData(self, packed_data):
        mat = unpack_and_validate_data(packed_data, n_valid_items = self.n_valid_bpms)
        self.storeDataInWaveforms(mat)

    def trigger(self):
        status_processed = DeviceStatus(self)

        def check_data(*args, **kws):
            """Check that the received data match the expected ones

            Could also be done during read status. I like to do it here
            as I see it as part of ensuring that good data were
            received
            """
            nonlocal status_processed

            data = self.packed_data.get()
            self.checkAndStorePackedData(data)

            status_processed.success = True
            status_processed.done = True

        status = super().trigger()
        status.add_callback(check_data)

        and_s = AndStatus(status, status_processed)
        return and_s


class BPMStorageRing( Device ):
    stat = Cpt(bpm_raw.BPMStatistics, "BPMZR", name = "stat")
    waveform = Cpt(BPMWaveform, "MDIZ2T5G", name = "wavefrom")

    hints = {"fields" : ["stat_read"]}
    def trigger(self, *args, **kwargs):
        r = self.waveform.trigger(*args, **kwargs)
        return r
