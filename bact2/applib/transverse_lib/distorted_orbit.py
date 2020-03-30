'''Utilities for closed orbit calculation

Todo:
    Use consistent variables: tune in mu or phi?
'''

import numpy as np


def closed_orbit_kick_unscaled(mu,  *, tune, mu_i):
    '''

    .. math::

         \\cos{\\left(
            \\pi Q -
                  \\left|{\\phi_i - \\phi{\\left (s \\right )}}
                 \\right|
         \\right)}
    '''
    mu = np.asarray(mu)

    qp = tune * np.pi
    dphi = mu - mu_i
    dphia = np.absolute(dphi)

    r = np.cos(qp - dphia)
    return r


def closed_orbit_kick(mu,  *, tune, beta_i, theta_i, mu_i):
    '''

    .. math::
        '\\sqrt{\\beta_i \\theta_i}' * closed_orbit_kick_unscaled

    '''
    cou = closed_orbit_kick_unscaled(mu, tune=tune, mu_i=mu_i)
    scale = beta_i * theta_i
    r = scale * cou
    return r


def closed_orbit_distortion(beta, mu,  *, tune, beta_i, theta_i, mu_i):
    '''Calculate orbit distortion created by one kicker
    '''
    tmp  = 2. * np.sin(tune * np.pi)
    devisor = 1. / tmp

    beta = np.asarray(beta)
    sq_beta = np.sqrt(beta)

    cok = closed_orbit_kick(mu, tune=tune, beta_i=beta_i, theta_i=theta_i, mu_i=mu_i)

    r = devisor * sq_beta
    r *= cok
    return r
