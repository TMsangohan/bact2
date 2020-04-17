from cart_pole_physics_model import CartPoleState, CartPolePhysics
from ophyd import Component as Cpt, Device, Signal
from ophyd.status import Status, AndStatus

from numpy import nan

class CartPole(Device):
    '''
    '''
    action    = Cpt(Signal, name='action',    value=nan)
    force     = Cpt(Signal, name='force',     value=nan)
    x         = Cpt(Signal, name='x',         value=nan)
    x_dot     = Cpt(Signal, name='x_dot',     value=nan)
    theta     = Cpt(Signal, name='theta',     value=nan)
    theta_dot = Cpt(Signal, name='theta_dot', value=nan)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.physics_model = CartPolePhysics()
        pm = self.physics_model

        # tmp = np_random.uniform(low=-0.05, high=0.05, size=(4,))
        # self.x.value, self.x_dot.value, self.theta.value, self.theta_dot.value = tmp

    def set(self, action):
        self.log.debug(f'Setting cartpole to {action}')
        
        self.action.value = action
        state = CartPoleState(x=self.x.get(), x_dot=self.x_dot.get(), 
                              theta=self.theta.get(), theta_dot=self.theta_dot.get())
        n_state = self.physics_model(state, action)

        stat_set = AndStatus(
            AndStatus(
                self.x.set(n_state.x),
                self.x_dot.set(n_state.x_dot)
            ),
            AndStatus(
                self.theta.set(n_state.theta),
                self.theta_dot.set(n_state.theta_dot)
            )
        )

        self.log.debug(f'Cartpole finished {action}')
        return stat_set

    def read(self):
        d = super().read()
        self.log.debug(f'Cart pool read {d}')
        return d


