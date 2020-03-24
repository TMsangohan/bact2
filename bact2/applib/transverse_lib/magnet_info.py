'''BESSY II magnet parameters

Todo:
   move to machine configuration
'''
import pandas as pd
import functools
import os.path


@functools.lru_cache(maxsize=1)
def magnet_parameters():

    names = ['power_converter', 'magnet', 'ring',
             'nominal_current', 'min_current', 'max_current',
             'transfer_function']

    path = '/home/mfp/Devel/bessy_ii'
    filename = 'ps-magnets.dbd'

    t_path = os.path.join(path, filename)
    df = pd.read_csv(t_path, names=names, delimiter=' ',
                     header=None, index_col=False)
    return df


def steerer_power_converter_to_steerer_magnet(name):
    name = name.upper()

    df = magnet_parameters()
    t_row = df.loc[df.power_converter == name, :]
    if t_row.shape[0] != 1:
        raise AssertionError(f'Found these {t_row} rows for supply {name}')
    magnet_name = t_row.magnet.values[0]
    return magnet_name


def magnet_transfer_function(magnet_name):

    df = magnet_parameters()
    t_row = df.loc[df.magnet == magnet_name, :]
    if t_row.shape[0] != 1:
        raise AssertionError(f'Found these {t_row} for magnet {magnet_name}')
    tf = t_row.transfer_function.values[0]
    return tf


def kicker_angle(magnet_name, current=None, magnet_length=None, ):
    '''derive steerer angle from magnet name and current for BESSY II
    Returns:
        angle in mrad

    Todo: check its validity!!

    '''

    assert(magnet_length is not None)
    # magnet_length = 0.16

    df = magnet_parameters()
    row = df.loc[df.magnet == magnet_name, ['transfer_function', 'max_current']]
    assert(row.shape[0] == 1)

    transfer_function, max_current = row.values.T
    if current is None:
        current = max_current

    b_main = 1.3042
    rho = 4.3545

    bdl = transfer_function * current * magnet_length
    # Magnet length would have to be fit to the available power
    # 2 * pi had to be added to:
    #  * the devisor as b * rho * 2 pi give the total magnet length
    #  * the nominator as 2 * pi give a full circle
    angle = bdl / (b_main * rho)

    angle = float(angle)

    return angle
