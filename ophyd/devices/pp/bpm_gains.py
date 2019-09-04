'''Load BESSY II scale factors

Warning:
    Work in progress. In its current form it is just used by the
    BPM devices to rescale the readings. It main purpose was to
    get the derived signals working.

Todo:
    Make the file path configurable
'''
import numpy as np
import logging
import os.path

logger = logging.getLogger('bact2')

#: directory where the data should be stored
_data_dir = os.path.dirname(__file__)

def load_bpm_gains(file_name = 'bpm_gains.txt', data_dir = _data_dir):
    '''load the bpm gains from the given file
    '''

    t_file = os.path.join(data_dir, file_name)
    logger.debug('Reading file {}'.format(t_file))

    gx, gy    = np.loadtxt(t_file, usecols = (1,2)).T
    bpm_names = np.loadtxt(t_file, usecols = (0,), dtype = np.object_)

    bpm_gains = {}
    for x, y, name in zip(gx, gy, bpm_names):
        bpm_gains[name] = np.array([x, y])
    del x, y, name

    return bpm_gains, gx, gy
