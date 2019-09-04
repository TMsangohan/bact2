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

    Todo:
        Check vector length and raise an appropriate Exception
        if these do not match
    '''

    def __init__(self, parent_attr, *, parent = None, parent_gain_attr = None, **kwargs):
        bin_signal = getattr(parent, parent_attr)
        super().__init__(derived_from = bin_signal, parent = parent, **kwargs)
        self._gain =  getattr(parent, parent_gain_attr)
        assert(self._gain is not None)

    def forward(self, values):
        return values * self._gain.value

    def inverse(self, values):
        return  values / self._gain.value

class BPMChannel( Device ):
    '''A channel (or coordinate) of the bpm

    The beam position monitor reading is split in the coordinates
        * x
        * y

    This is made, as each channel requires the following signals:
        * pos:     the actual position
        * rms:     the rms of the actual position
        * pos_raw: raw reading of the position
        * rms_raw: rms of the raw reading
        * gain:    a vector for rescaling the device


    Warning:
        It is the users responsibility to set the gains correctly!
    '''

    _default_config_attrs = ('gain',)

    #: Relative beam offset as measured by the beam position monitors
    pos_raw = Cpt(Signal, name = 'pos_raw')
    #: and its rms value
    rms_raw = Cpt(Signal, name = 'rms_raw')

    #: gains for the channels
    gain = Cpt(Signal, name = 'gain', value = 1.0)

    #: processed data: already in mm
    pos = Cpt(DerivedSignalLinear, parent_attr = 'pos_raw', parent_gain_attr = 'gain', name = 'pos')
    rms = Cpt(DerivedSignalLinear, parent_attr = 'rms_raw', parent_gain_attr = 'gain', name = 'rms')


    def trigger(self):
        raise NotImplementedError('Use BPMWaveform instead')

class BPMWaveform(  bpm_raw.BPMPackedData ):
    """Measurement data for the beam position monitors

    Todo:
        Reference to the coordinate system
        Clarify status values
        Clarify why data are given for "non existant monitors"
    """

    #: Number of valid beam position monitors
    n_valid_bpms = 128

    #: All data for x
    x = Cpt(BPMChannel, 'x')
    #: All data for y
    y = Cpt(BPMChannel, 'y')

    #: Data not sorted into the different channels
    intensity_z = Cpt(Signal, name = "z")
    intensity_s = Cpt(Signal, name = "s")
    status      = Cpt(Signal, name = "status")

    #: gains as found in the packed data. The gains for recalculating
    #: the values are found in the BPMChannels
    gain_raw    = Cpt(Signal, name = "gain")

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

        self.x.pos_raw.put(  mat[0])
        self.y.pos_raw.put(  mat[1])
        self.intensity_z.put(mat[2])
        self.intensity_s.put(mat[3])
        self.status.put(       stat)
        self.gain_raw.put(   mat[5])
        self.x.rms_raw.put(  mat[6])
        self.y.rms_raw.put(  mat[7])


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
