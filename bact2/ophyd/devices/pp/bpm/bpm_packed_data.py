import numpy as np
from numpy.core.records import fromarrays
from ...utils import process_vector


def unpack_and_validate_data(packed_data, n_valid_items=None, indices=None):
    """Split the packed data up to a matrix of bpm waveforms

    Args :
        packed_data : the data as received by the BPM

    Returns :
        mat : a matrix with the  different signals as row vectors

    See :func:`packed_data_to_named_array` for convenient procecssing of packed
    data to named array
    """
    mat1 = process_vector.unpack_vector_to_matrix(packed_data, n_vecs=2)
    with_data = mat1[0, :]
    unused = mat1[1, :]
    process_vector.check_unset_elements(unused, n_valid_rows=n_valid_items,
                                        unset_elements_value=0)
    del unused

    mat = process_vector.unpack_vector_to_matrix(with_data, n_vecs=8)
    if indices is not None:
        mat = np.take(mat, indices, axis=1)

    return mat

    # Why does the check below fail.
    # Apparaently garbage in the left over comlums

    for col in mat:
        # process_vector.check_unset_elements(col,
        #                                    n_valid_rows=self.n_valid_bpms,
        #                                    unset_elements_value=0)
        #
        pass


def data_to_named_array(mat):
    '''preprocessed packed data to named array

    See :func:`packed_data_to_named_array` for convenient procecssing of packed
    data to named array

    Args:
        mat: a matrix with the appropriate number of elements

    '''
    names = ['x_pos_raw', 'y_pos_raw', 'intensity_z', 'intensity_s', 'stat']
    names += ['gain_raw', 'x_rms_raw', 'y_rms_raw']

    # At least the first dimension
    rows = [mat[row] for row in range(mat.shape[0])]
    data = fromarrays(rows, names=names)

    return data


def packed_data_to_named_array(packed_data, n_valid_items=None, indices=None):
    '''check packed bpm data and split it to a named array
    '''
    mat = unpack_and_validate_data(packed_data, n_valid_items=n_valid_items,
                                   indices=indices)
    t_array = data_to_named_array(mat)
    return t_array


#: default bit gain for bpms. Scales raw readings to mm scale
#: These can be still wrong by factors, but are then in the appropriate decade
bit_gain_default = 2**15/10.0


def raw_to_scaled_data_channel(values, gain, offset, bit_gain=None):
    '''BPM raw to physics coordinates

        BPM data are first scaled from raw data to mm.
        Then the offset is subtracted.
    '''

    if bit_gain is None:
        t_gain = gain
    else:
        t_gain = gain * bit_gain

    del gain, bit_gain

    scaled = values / t_gain
    r = scaled - offset
    return r


def raw_to_scaled_data(a_array, bpm_parameters, bit_gain=None):
    '''Scale the channel data for the bpms

    Args:
       a_array: a record array containing the raw data of the bpm's
       bpm_parameters: a record array containing the rescale values
       bit_gain: conversion factor from bit to gain parameters
    '''

    conv = raw_to_scaled_data_channel

    x_scale = bpm_parameters['x_scale']
    x_offset = bpm_parameters['x_offset']
    x_pos = conv(a_array['x_pos_raw'], x_scale, x_offset, bit_gain=bit_gain)
    x_rms = conv(a_array['x_rms_raw'], x_scale, 0.0, bit_gain=bit_gain)

    del x_scale, x_offset

    y_scale = bpm_parameters['x_scale']
    y_offset = bpm_parameters['x_offset']
    y_pos = conv(a_array['y_pos_raw'], y_scale, y_offset, bit_gain=bit_gain)
    y_rms = conv(a_array['y_rms_raw'], y_scale, 0.0, bit_gain=bit_gain)

    del y_scale, y_offset

    t_names = ['x_pos', 'y_pos',  'x_rms', 'y_rms']
    res = fromarrays([x_pos, y_pos, x_rms, y_rms], names=t_names)
    return res
