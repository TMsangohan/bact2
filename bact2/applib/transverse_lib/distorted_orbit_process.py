'''A more data centric approach for kick calculations
'''

from . import distorted_orbit
import numpy as np
from  dataclasses import dataclass

pi2 = np.pi * 2


@dataclass
class KickParameters:
    '''
    '''
    #: betatron function at the kick
    beta_i : float
    #: phase advance at the kick
    mu_i : float
    #: kick angle
    theta_i : float
    #: position in the ring
    s : float


@dataclass
class MachineDescriptionForPlane:
    '''
    '''
    #: tune of the machine
    Q : float
    #: betatron function of the machine
    beta : np.ndarray
    #: phase advance of the machine
    mu : np.ndarray
    #: info useful for plotting
    s : np.ndarray

def kick_info(df_sel, kick, columns=None):
    '''

    I do not see any advantage in exporting this helper func
    '''

    assert(columns is not None)
    row = df_sel.loc[:, columns]
    beta, mu = row.values.T
    s = df_sel.loc[:, 's'].values
    s = float(s)
    kick = KickParameters(beta_i=beta, mu_i=mu, theta_i=kick, s=s)
    return kick


def machine_info(df, columns=None):
    assert(columns is not None)

    # I assume that the data frame is sorted
    df_sel = df.loc[:, columns]
    s = df.loc[:, 's'].values
    beta, mu = df_sel.values.T
    Q = mu[-1] / pi2

    r = MachineDescriptionForPlane(beta=beta, mu=mu, Q=Q, s=s)
    return r


def orbit_distortion_for_kicker(machine_description, kick_parameters):
    beta = machine_description.beta
    Q = machine_description.Q
    mu = machine_description.mu
    beta_i = kick_parameters.beta_i
    theta_i = kick_parameters.theta_i
    mu_i = kick_parameters.mu_i
    f = distorted_orbit.closed_orbit_distortion
    co = f(beta, mu, tune=Q, beta_i=beta_i, theta_i=theta_i, mu_i=mu_i)
    return co
