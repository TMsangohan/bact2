"""Beam position monitors

Currently much focused on the implementation in BESSY II
"""
from ophyd import Component as Cpt, Signal, Device, DerivedSignal
from ophyd.status import DeviceStatus, AndStatus

from ..raw import bpm as bpm_raw
from ..utils import process_vector
import numpy as np

import functools

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


class DerivedSignalLinear( DerivedSignal ):
    '''Rescale a derived signal using linear gains

    Args:
        parent_attr: the name of the signal in the parent from
                     which to derive from.
        gain:        a *vector* of gains

    Currently used for rescaling the BPM's.

    Warning:
        If the vector of gains does not contain a sufficient number
        of entries, the number of values will be truncated!
    '''

    def __init__(self, parent_attr, *, parent = None, gain = None, **kwargs):
        bin_signal = getattr(parent, parent_attr)
        super().__init__(derived_from = bin_signal, parent = parent, **kwargs)
        assert(gain is not None)
        self._gain = gain

    def _cutVector(self, values):
        values = np.asarray(values)
        l = len(self._gain)
        return values[:l]

    def forward(self, values):
        values = self._cutVector(values)
        return values * self._gain

    def inverse(self, values):
        values = self._cutVector(values)
        return  values / self._gain

@functools.lru_cache(maxsize=1)
def _get_gains():
    from . import bpm_gains
    bpm_gains, gx, gy = bpm_gains.load_bpm_gains()
    return gx, gy

class BPMWaveform(  bpm_raw.BPMPackedData ):
    """Measurement data for the beam position monitors

    Todo:
        Reference to the coordinate system
        Clarify status values
        Clarify why data are given for "non existant monitors"
    """

    #: Number of valid beam position monitors
    n_valid_bpms = 128


    #: Relative horizontal beam offset as measured by the beam position monitors
    pos_x_raw   = Cpt(Signal, name = "dx")
    #: Relative vertical beam offset as measured by the beam position monitors
    pos_y_raw   = Cpt(Signal, name = "dy")
    #:
    intensity_z = Cpt(Signal, name = "z")
    intensity_s = Cpt(Signal, name = "s")
    status      = Cpt(Signal, name = "status")
    gain        = Cpt(Signal, name = "gain")
    rms_x_raw   = Cpt(Signal, name = "rms_x_raw")
    rms_y_raw   = Cpt(Signal, name = "rms_y_raw")


    pos_x = Cpt(DerivedSignalLinear, parent_attr = 'pos_x_raw', name = "x", gain = _get_gains()[0])
    pos_y = Cpt(DerivedSignalLinear, parent_attr = 'pos_y_raw', name = "y", gain = _get_gains()[1])

    rms_x = Cpt(DerivedSignalLinear, parent_attr = 'rms_x_raw', name = "rms_x", gain = _get_gains()[0])
    rms_y = Cpt(DerivedSignalLinear, parent_attr = 'rms_y_raw', name = "rms_y", gain = _get_gains()[1])


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

        self.pos_x.put(      mat[0])
        self.pos_y.put(      mat[1])
        self.intensity_z.put(mat[2])
        self.intensity_s.put(mat[3])
        self.status.put(         stat)
        self.gain.put(       mat[5])
        self.rms_x.put(      mat[6])
        self.rms_y.put(      mat[7])


    def checkAndStorePackedData(self, packed_data):
        mat = unpack_and_validate_data(packed_data, n_valid_items = self.n_valid_bpms)
        return self.storeDataInWaveforms(mat)

    def trigger(self):
        status_processed = DeviceStatus(self, timeout = 5)

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




#class ScaledBPMWaveForm( BPMWaveform ):
#    '''
#    '''
#    #: Relative horizontal beam offset as measured by the beam position monitors in millimeters
#    pos_x_mm = Cpt(DerivedSignalLinear, derived_from = BPMWaveform.pos_x, name = "dx", gain = 1.0)
#    #: Relative vertical beam offset as measured by the beam position monitors
#    pos_y_mm = Cpt(DerivedSignalLinear, derived_from = BPMWaveform.pos_y, name = "dy", gain = 1.0)



class BPMStorageRing( Device ):
    stat = Cpt(bpm_raw.BPMStatistics, "BPMZR", name = "stat")
    waveform = Cpt(BPMWaveform, "MDIZ2T5G", name = "wavefrom")

    # scaled_waveform = Cpt(ScaledBPMWaveForm, "MDIZ2T5G", name = "sw")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # hints = {"fields" : ["stat_read"]}
    def trigger(self, *args, **kwargs):
        r = self.waveform.trigger(*args, **kwargs)
        return r

    def read(self):
        r = super().read()
        # print('r {}'.format(r))
        return r
