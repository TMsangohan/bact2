"""Beam position monitors

Currently much focused on the implementation in BESSY II

Todo:
   investigate how it can be adapted for MLS
"""
from ophyd import Component as Cpt, Signal, Device
from ophyd.status import DeviceStatus, AndStatus

from ...raw import bpm as bpm_raw
from ...utils import process_vector
from ...utils.derived_signal import DerivedSignalLinear
from .bpm_parameters import create_bpm_config

import numpy as np
import functools
import enum

def unpack_and_validate_data(packed_data, n_valid_items = None, indices = None):
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
    if indices is not None:
        mat = np.take(mat, indices, axis=1)
    for col in mat:
        # Why does that currently not work ?
        # process_vector.check_unset_elements(col, n_valid_rows = self.n_valid_bpms, unset_elements_value = 0)
        pass
    return mat



class BPMStatusBits(enum.IntEnum):
    '''BESSY II beam position monitors status bits

    Todo:
        Check if status bits above 2 are still in use
    '''
    #: short form: `AGC`
    automatic_gain_control = 0
    #: short form: `Pwr`
    power  = 1
    #: short form `STmode`
    single_turn_mode = 2
    #: short from `DiagMode`
    diag_mode = 3
    #: short form `ADRA0`
    adr_a0 = 4
    #: short form `ADRA1`
    adr_a1 = 5
    #: short form `CS`
    cs_select = 6
    #: short form `Live`
    live = 7


class BPMChannelScale( DerivedSignalLinear ):
    ''' Reduce repetition of typing for
    * gain
    * bit_gain
    * offset
    '''
    def __init__(self, *args, **kwargs):

        for sig_name in ['gain', 'bit_gain', 'offset']:
            kwargs.setdefault('parent_{}_attr'.format(sig_name), sig_name)
        
        super().__init__(*args, **kwargs)

class BPMChannel( Device ):
    '''A channel (or coordinate) of the bpm

    The beam position monitor reading is split in the coordinates
        * x
        * y

    This is made, as each channel requires the following signals:
        * pos:      the actual position
        * rms:      the rms of the actual position
        * pos_raw:  raw reading of the position
        * rms_raw:  rms of the raw reading
        * gain:     a vector for rescaling the device from 
        * bit_gain: a rough scale from mm to bit

    Warning:
        Let :class:`BPMWavefrom` use it
        It is the users responsibility to set the gains correctly!
        
    '''

    _default_config_attrs = ('gain', 'offset', 'scale')

    #: Relative beam offset as measured by the beam position monitors
    pos_raw = Cpt(Signal, name = 'pos_raw')
    #: and its rms value
    rms_raw = Cpt(Signal, name = 'rms_raw')
    
    #: gains for the channels
    gain   = Cpt(Signal, name = 'gain', value = 1.0)
    offset = Cpt(Signal, name = 'offset', value = 0.0)

    #: scale bits to mm
    bit_gain  = Cpt(Signal, name = 'bit_gain', value = 2**15/10)

    #: processed data: already in mm
    pos = Cpt(BPMChannelScale, parent_attr = 'pos_raw', name = 'pos')
    rms = Cpt(BPMChannelScale, parent_attr = 'rms_raw', name = 'rms')

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

    ds      = Cpt(Signal, name = 'ds', value = np.nan)
    names   = Cpt(Signal, name = 'names', value = [])
    indices = Cpt(Signal, name = 'indices', value = [])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check its there and an int
        self.n_valid_bpms = int(self.n_valid_bpms)
        assert(self.n_valid_bpms > 0)

        self.setConfigData()

    def setConfigData(self):        
        rec = create_bpm_config()
        self.names.put(rec['name'])
        self.ds.put(rec['ds'])
        idx = rec['idx']
        self.indices.put(idx - 1)
        self.x.gain.put(rec['x_scale'])
        self.y.gain.put(rec['y_scale'])
        self.x.offset.put(rec['x_offset'])
        self.y.offset.put(rec['y_offset'])
        
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
        
        indices = self.indices.value
        if len(indices) == 0:
            indices = None
            
        mat = unpack_and_validate_data(packed_data, n_valid_items = self.n_valid_bpms,
                                       indices = indices)
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
