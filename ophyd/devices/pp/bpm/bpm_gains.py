'''Load BESSY II scale factors

Warning:
    Work in progress. In its current form it is just used by the
    BPM devices to rescale the readings. It main purpose was to
    get the derived signals working.

Todo:
    Use pkgutil for resource
'''
import numpy as np
import logging
import os.path
import pkgutil

logger = logging.getLogger('bact2')

#: directory where the data should be stored
_data_dir = os.path.dirname(__file__)

def load_bpm_gains(file_name = 'bpm_gains.txt', data_dir = _data_dir):
    '''load the bpm gains from the given file

    Todo:
        Switch to pgkutil for resource selection
       
    
    Returns: a structured numpy array.

    
    The returned array contains the following entries:
        * `name`: name of the beam position monitor
        * `x_scale`: scale in x axis
        * `y_scale`: scale in y axis
    '''

    t_file = os.path.join(data_dir, file_name)
    logger.warning('Module {} Reading file {}'.format(__name__, t_file))

    dtypes = np.dtype({
        'names'   : ['name', 'x_scale',  'y_scale' ],
        'formats' : ['U20',   np.float_,  np.float_]
        }
    )

    bpm_gains = np.loadtxt(t_file, dtype = dtypes)
    return bpm_gains
