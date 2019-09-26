import numpy as np
from . import bpm_config


#: scale raw bpm bits to mm
#: 10 mm equals 2**15
bit_scale = 10/2**15

def create_bpm_config():
    '''Beam position monitor as an array of records

    The calculation from BPM readings to physical data is handled by
    :class:`ophyd.devices.utils.derived_signal.DerivedSignalLinearBPM`

    Returns:
         a structured numpy array

   The returned array contains the following entries:
        * `name: name of the beam position monitor
        * `x_state`: scale in x axis
        * `y_state`: scale in y axis
        * `ds` : s position in the ring
        * `x_scale`: scale in x axis
        * `y_scale`: scale in y axis
        * `x_offset`: offset in x axis
        * `y_offset`: offset in y axis


    Todo:
        Define how to treat scale and offset. Please note that
        :mod:Ophyd uses :meth:`DerivedSignal.inverse` to derive the
        physical data from the raw readings of the device.
    '''

    dtypes = np.dtype({
        'names'   : ['name', 'x_state', 'y_state',  'ds',      'idx',    'x_scale',  'y_scale', 'x_offset', 'y_offset'],
        'formats' : ['U20',   np.bool_,  np.bool_,   np.float_, np.int_,  np.float_,  np.float_, np.float_,  np.float_]
        }
    )

    l = len(bpm_config.bpm_conf)
    data = np.zeros((l,), dtype = dtypes)
    for i in range(l):
        entry = bpm_config.bpm_conf[i]
        data[i] = entry + (0,0)

    del entry, i, l

    # The scale factors are stored as multipliers ...
    # The BPM class expects them as deviders
    data['x_scale'] = 1 / data['x_scale']
    data['y_scale'] = 1 / data['y_scale']

    for name in bpm_config.bpm_offset.keys():
        x_offset, y_offset = bpm_config.bpm_offset[name]

        idx = data['name'] == name
        line = data[idx]
        assert(name == line['name'])

        line['x_offset'] = x_offset
        line['y_offset'] = y_offset
        data[idx] = line

    del idx, x_offset, y_offset, line, name
    # deselect deactivated bpms
    valid_bpms = data['x_state'] & data['y_state']
    reduced_bpms = data[valid_bpms]
    del data

    # only valid bpms beyond this point
    assert(sum(reduced_bpms['x_state']) == reduced_bpms.shape[0])
    assert(sum(reduced_bpms['x_state']) == reduced_bpms.shape[0])


    ds_sort = np.argsort(reduced_bpms['ds'])
    sorted_bpms = np.take(reduced_bpms, ds_sort)
    del ds_sort
    del reduced_bpms

    return sorted_bpms

if __name__ == '__main__':
    l = 10
    dtypes = np.dtype({
        'names'   : ['name', 'state_x', 'state_y', 'ds',     'idx',    'x_scale',   'y_scale'],
        'formats' : ['U20',   np.bool_,  np.bool_,  np.float_, np.int_,  np.float_,  np.float_]
        }
    )
    data = np.array(l, dtype = dtypes)

    s_bpm = create_bpm_config()
    idx = s_bpm['idx']
    print('{:d} # names'.format(len(s_bpm['name'])))
    print('{:d} # indices {:d} unique ones'.format(len(idx), len(set(idx))))
    print('{:d} # scale_x'.format(len(s_bpm['x_scale'])))
