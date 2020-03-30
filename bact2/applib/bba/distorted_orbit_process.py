from ..transverse_lib import distorted_orbit_process
from ..transverse_lib.process_model_fits import prepare_bpm_data
from dataclasses import dataclass
from scipy.optimize import lsq_linear
import numpy as np

import logging
import importlib
importlib.reload(distorted_orbit_process)

logger = logging.getLogger('bact2')

#: Ocelot naming conventions
beta_x, beta_y = 'beta_x', 'beta_y'
mu_x, mu_y = 'mux', 'muy'


def machine_info_xy(twiss_df):

    machine_info = distorted_orbit_process.machine_info
    machine_x = machine_info(twiss_df, columns=[beta_x, mu_x])
    machine_y = machine_info(twiss_df, columns=[beta_y, mu_y])

    return machine_x, machine_y


def quadrupole_equivalent_kicks(twiss_df, quadrupole_name, *, name_column='id'):
    '''

    Args:
        twiss_df        : an instanace of a :class:``pandas.DataFrame`
                          containing the twiss parameters along the ring
                          The column naming follows currently the entries of
                          :class:`ocelot.cpbd.beam.Twiss`
        quadrupole_name : the name of the quadrupole to handle

    Returns: (
               :class:`distorted_orbit_process.KickParameters`
               :class:`distorted_orbit_process.KickParameters`
    )

    Warning:
        The user has to set the kick angle afterwards
    '''
    df_sel = twiss_df.loc[twiss_df.loc[:, name_column] == quadrupole_name]

    # Test that only one quadruole was selected and that it is the expected one
    tmp = set(df_sel.loc[:, name_column])
    n_names = list(tmp)
    assert(len(n_names) == 1)
    quadrupole_name_test = n_names[0]
    assert(quadrupole_name == quadrupole_name_test)
    del quadrupole_name_test

    # Expecting exactly one row
    assert(df_sel.shape[0] == 1)
    del tmp, n_names

    # the kicks ...
    kick_info = distorted_orbit_process.kick_info
    d_kick_x = kick_info(df_sel, 0, columns=[beta_x, mu_x])
    d_kick_y = kick_info(df_sel, 0, columns=[beta_y, mu_y])

    return d_kick_x, d_kick_y


def distorted_orbit_for_quad(twiss_df, quadrupole_name, *,
                             kick_x=None, kick_y=None):
    '''Single function does all
    '''
    raise

    # Machine functions
    machine_x, machine_y =  machine_info_xy(twiss_df)

    d_kick_x, d_kick_y = quadrupole_equivalent_kicks(twiss_df, quadrupole_name)

    d_kick_x.theta_i = kick_x
    d_kick_y.theta_i = kick_y
    f = distorted_orbit_process.orbit_distortions_for_kicker
    co_x = f(d_kick_x, machine_x)
    co_y = f(d_kick_y, machine_y)

    return co_x, co_y


def model_kick(twiss_df, quadrupole_name, guessed_angle):
    func = quadrupole_equivalent_kicks
    kx, ky  = func(twiss_df, quadrupole_name=quadrupole_name)
    kx.theta_i = guessed_angle
    ky.theta_i = guessed_angle
    kx, ky
    return kx, ky


@dataclass
class MachineModel:
    # Orbit: typically for the total machine
    orbit : object
    # Orbit at bpm's
    bpm   : object
    # Associated Kick
    kick  : object


@dataclass
class MachineResults(MachineModel):
    # Measured bpm data
    bpm_data : np.ndarray
    # Guessed kick strength
    guessed_angle : float
    # excitation currents of the quadruole
    dI : np.ndarray
    # results of the fit as returned by the rpocedure
    fit_result : object


@dataclass
class MachineModelXY:
    x : MachineModel
    y : MachineModel


@dataclass
class MachineResultsXY:
    x : MachineResults
    y : MachineResults


def bpm_data_process(data, dI, eps=1e-3):

    adI = np.absolute(dI)
    idx = adI < eps
    offset_data = data[idx, :]
    offset = offset_data.mean(axis=0)
    diff = data - offset[np.newaxis, :]
    return diff


def model_data_process(data, scale=None):
    # For the different exitation levels
    assert(scale is not None)

    scale = np.asarray(scale)
    data_2d = data[np.newaxis,:] * scale[:, np.newaxis]
    model_data = np.ravel(data_2d)
    const_part = np.ones(model_data.shape, model_data.dtype)
    model_data_linear = np.array([model_data, const_part]).T
    return model_data_linear


def fit_single_plane(co_bpm, bpm_data, dI=None, scale_bpm=None):

    assert(dI is not None)

    if scale_bpm is None:
        scale_bpm = 1.0/1000.
    scale_bpm = float(scale_bpm)

    measurement_data = bpm_data_process(bpm_data, dI).ravel()
    model_data_linear = model_data_process(co_bpm, scale=dI)

    measurement_data = measurement_data * scale_bpm
    try:
        r = lsq_linear(model_data_linear, measurement_data)
    except Exception:
        tmp = model_data_linear.shape, measurement_data.shape
        txt = "model shape {} measurement data shape {}".format(*tmp)
        txt2 = "bpm data shape {}".format(bpm_data.shape)
        logger.error(txt)
        raise
    assert(r.status == 3)
    return r


def process_single_plane(machine_models, kick, bpm_data,
                         dI=None, scale_bpm=None):
    func = distorted_orbit_process.orbit_distortion_for_kicker
    co = func(machine_models.orbit, kick)
    co_bpm = func(machine_models.bpm, kick)

    r = fit_single_plane(co_bpm, bpm_data, dI=dI)
    return MachineResults(orbit=co, bpm=co_bpm, bpm_data=bpm_data,
                          dI=dI, guessed_angle=None, kick=kick,
                          fit_result=r)


def process_single(twiss_df, data_df, quadrupole_name, machine_models,
                   guessed_angle=1e-6):
    '''

    Todo:
        dataclass as input
    '''
    df_sel = data_df.loc[(data_df.mux_selector_selected == quadrupole_name), :]
    dI = df_sel.mux_power_converter_setpoint.values

    bpm_data, bpm_data_m = prepare_bpm_data(df_sel)

    mod_x, mod_y = machine_models.x, machine_models.y
    kx, ky  = model_kick(twiss_df, quadrupole_name=quadrupole_name,
                         guessed_angle=guessed_angle)

    rx = process_single_plane(mod_x, kx, bpm_data_m.x, dI=dI)
    rx.guessed_angle = guessed_angle
    ry = process_single_plane(mod_y, ky, bpm_data_m.y, dI=dI)
    ry.guessed_angle = guessed_angle

    return MachineResultsXY(x=rx, y=ry)
