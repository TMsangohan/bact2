import numpy as np
from dataclasses import dataclass

@dataclass
class CartPoleState:
    x : float
    x_dot : float
    theta : float
    theta_dot : float

    @property
    def values(self):
        tmp = self.x, self.x_dot, self.theta, self.theta_dot
        return tmp

class CartPolePhysics:
    '''Phsics engine of the cartpool
    '''
    def __init__(self):
        # Today's special value
        # If we'd work for ESA it should be adjustable
        self.gravity = 9.8
        self.masscart = 1.0
        self.masspole = 0.1
        self.total_mass = (self.masspole + self.masscart)
        self.length = 0.5 # actually half the pole's length
        self.polemass_length = (self.masspole * self.length)
        self.force_mag = 10.0
        self.tau = 0.02  # seconds between state updates
        self.kinematics_integrator = 'euler'

    def __call__(self, state, action):

        x = state.x
        x_dot = state.x_dot
        theta = state.theta
        theta_dot = state.theta_dot

        force = self.force_mag if action==1 else -self.force_mag
        
        costheta = np.cos(theta)
        sintheta = np.sin(theta)
        
        temp = (force + self.polemass_length * theta_dot**2 * sintheta) / self.total_mass
        thetaacc = (self.gravity * sintheta - costheta * temp) / (self.length * (4.0/3.0 - self.masspole * costheta**2 / self.total_mass))
        xacc  = temp - self.polemass_length * thetaacc * costheta / self.total_mass

        if self.kinematics_integrator == 'euler':
            x  = x + self.tau * x_dot
            x_dot = x_dot + self.tau * xacc
            theta = theta + self.tau * theta_dot
            theta_dot = theta_dot + self.tau * thetaacc
        else: # semi-implicit euler
            x_dot = x_dot + self.tau * xacc
            x  = x + self.tau * x_dot
            theta_dot = theta_dot + self.tau * thetaacc
            theta = theta + self.tau * theta_dot

        state = CartPoleState(x=x, x_dot=x_dot, theta=theta, theta_dot=theta_dot)
        return state
