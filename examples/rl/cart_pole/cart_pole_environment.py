from bact2.bluesky.plans.environement import Environment

from cart_pole_physics_model import CartPoleState
from gym.utils import seeding
import numpy as np


class CartPoleEnv(Environment):

    _observation_space = np.zeros((4,)) + np.nan
    _action_space = 2 # Why the hell 2?

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.theta_threshold_radians = 12 * 2 * np.pi / 360
        self.x_threshold = 2.4
    
    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        r = [seed]
        self.log.warning(f'Seed {r}')
        return r

    def extractState(self, dic):
        print('measured', dic)

        dets = self.detectors
        assert(len(dets) == 1)
        det = dets[0]
        det_name = det.name
        try:
            x         = dic[f'{det_name}_x']['value']
        except Exception:
            self.log.error(f'Extraction failed from dic {dic}')

        x_dot     = dic[f'{det_name}_x_dot']['value']
        theta     = dic[f'{det_name}_theta']['value']
        theta_dot = dic[f'{det_name}_theta_dot']['value']

        state = CartPoleState(x=x, x_dot=x_dot, theta=theta, theta_dot=theta_dot)
        return state

    def storeInitialState(self, dic):
        state = self.extractState(dic)
        self.state_to_reset_to = state.values

    def getStateToResetTo(self):
        start = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        return start

    def computeRewardTerminal(self, dic):

        state = self.extractState(dic)
        x = state.x
        theta = state.theta

        done =  x < -self.x_threshold \
                or x > self.x_threshold \
                or theta < -self.theta_threshold_radians \
                or theta > self.theta_threshold_radians
        done = bool(done)

        if not done:
            reward = 1.0
        elif self.steps_beyond_done is None:
            # Pole just fell!
            self.steps_beyond_done = 0
            reward = 1.0
        else:
            if self.steps_beyond_done == 0:
                txt = (
                    """You are calling 'step()' even though this environment
 has already returned done = True. You should always call 'reset()' once you
 receive 'done = True' -- any further steps are undefined behavior."""
                )
                self.log.warn(txt)
            self.steps_beyond_done += 1
            reward = 0.0

        return reward, done

    def computeState(self, dic):
        return self.extractState(dic).values

