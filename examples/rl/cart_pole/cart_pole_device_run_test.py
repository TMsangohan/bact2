import logging
logging.basicConfig(level='INFO')

from bact2.bluesky.plans.threaded_environement import run_environement
#from bact2.bluesky.plans.multiprocessor_environement import run_environement

from bluesky import RunEngine
from cart_pole_device import CartPole
from cart_pole_environment import CartPoleEnv
import logging
logger = logging.getLogger('bact2')

import functools

import sys
recursion_limit = sys.getrecursionlimit()
max_recursion = recursion_limit * 2
sys.setrecursionlimit(max_recursion)

def run_test(env, *, log=None):

    assert(log is not None)

    env.seed()
    log.info('\nSetup start\n')
    env.setup()
    log.info('\nSetup succeded\n')
    env.reset()
    log.info('\nReset succeded\n')
    env.step(.2)
    log.info('\nStep succeded\n')
    env.done()
    log.info('\nDone succeded\n')
    return

def main():
    cart_pole = CartPole(name = 'cp')

    log = logging.getLogger('bact2')

    RE = RunEngine({})
    RE.log.setLevel('DEBUG')
    cart_pole.log = RE.log


    stm = [cart_pole.x, cart_pole.x_dot, cart_pole.theta, cart_pole.theta_dot]
    cpst = CartPoleEnv(detectors=[cart_pole], motors=[cart_pole], 
    state_motors=stm)

    partial = functools.partial(run_test, cpst, log=RE.log)
    RE(run_environement(cpst, partial, log=RE.log))

if __name__ == '__main__':
    main()

