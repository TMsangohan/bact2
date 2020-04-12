'''OpenAI compatible environment
'''
from bluesky import plan_stubs as bps, preprocessors as bpp
import functools

import super_state_machine.machines
import enum
import logging
logger = logging.getLogger('bact2')

def per_step_plan(detectors, motors, actions, *args, log=None, **kwargs):
    '''execute one step and push result into queue

    Args:
        device : a ophyd (environment) device
        sink :  an object consuming the return argument

    '''
    if log is None:
        log = logger

    motors = list(motors)
    action = list(actions)

    # There should be a func
    l = []
    for m, a in zip(motors, action):
        l.extend([m, a])
    args = tuple(l)

    log.info(f'Executing mv {args}')
    yield from bps.mv(*args)

    r = (yield from bps.trigger_and_read(detectors))
    log.info(f'Read {detectors} to {r}')

    return r


def setup_plan(detectors, motors, *args, log=None, **kwargs):
    '''retrieve the actual status

    Args:
        device : a ophyd (environment) device
        sink :  an object consuming the return argument

    '''
    if log is None:
        log = logger


    yield from bps.checkpoint()
    log.info(f'Reading detectors {detectors}')
    r =  (yield from bps.trigger_and_read(detectors))
    log.info(f'setup returned {r}')
    return r


def reset_plan(detectors, state_motors, saved_state,  *args, log=None, **kwargs):
    '''plan to revert environement to orginal state
    '''
    if log is None:
        log = logger

    log.info(f'Executing reset plan on {state_motors} and saved_state {saved_state}')
    r = (yield from per_step_plan(detectors, state_motors, saved_state))
    log.info(f'Reset plan read {r}')
    return r


def teardown_plan(detectors, motors, actions, state_motors, state_actions,  *args, log=None, **kwargs):
    '''Typically: nothing to do

    Args:
        detectors: the
    Todo:
        Consider resetting to original state
    '''
    if log is None:
        log = logger


class EnvironmentState(super_state_machine.machines.StateMachine):
    class States(enum.Enum):
        UNDEFINED = 'undefined'
        SETUP = 'setting_up'
        TEARDOWN = 'tearing_down'
        RESETTING = 'resetting'
        INITIALISED = 'initialised'
        STEPPING = 'stepping'
        DONE = 'done'
        FAILED = 'failed'

    class Meta:
        initial_state = 'undefined'
        transitions =  {
            'undefined' : ['resetting', 'setting_up', 'tearing_down', 'failed'],
            'setting_up' : ['initialised', 'tearing_down', 'failed'],
            'resetting' : ['initialised', 'tearing_down', 'failed'],
            'initialised' : ['stepping', 'done', 'resetting', 'tearing_down', 'failed'],
            'stepping' : ['stepping', 'done', 'tearing_down', 'failed'],
            'done' : ['resetting', 'setting_up', 'tearing_down', 'failed'],
            'tearing_down' : ['undefined', 'failed'],
            'failed' : ['undefined', 'resetting', 'tearing_down', 'failed'],
        }


class Environment:
    '''OpenAI enviroment emmitting bluesky plans for real measurements

    The device has to have the same signature as the device
        :class:`bact2.ophyd.utils.environement.`

    '''
    def __init__(self, *, detectors, motors, state_motors, log=None,
                per_step_plan=per_step_plan,
                reset_plan=reset_plan,
                setup_plan=setup_plan,
                teardown_plan=teardown_plan,
                user_args=(),
                user_kwargs={},
                plan_executor=None,
                ):

        self.detectors = detectors
        self.motors = motors
        self.state_motors = state_motors

        if log is None:
            log = logger
        self.log = log

        self.per_step_plan = per_step_plan
        self.reset_plan = reset_plan
        self.setup_plan = setup_plan
        self.teardown_plan = teardown_plan

        user_kwargs.setdefault('log', log)
        self.user_args = user_args

        self.user_kwargs = user_kwargs

        self.state_to_reset_to = None

        self._executor = plan_executor

        self.state = EnvironmentState()

    #-------------------------------------------------------------------------
    # Methods to override in a derived class
    def storeInitialState(self, dic):
        '''Extract the inital state read back from the device

        dic :
            the dictonary as read from the devices

        Typical implementation: identify the set values of the motors in the
        devices. Store them in the order as found in self.motors
        '''
        raise NotImplementedError('implement in derived class')
        # Extract the data you require to reset to
        self.state_to_reset_to

    def getStateToResetTo(self):
        '''State to reset environment to

        Typically returns the state stored by storeInitialState
        Please note that the dic returned by storeInitialState will
        contain much more information than just the settings of the
        motors
        '''
        raise NotImplementedError('implement in derived class')
        assert(self.state_to_reset_to is not None)
        return self.state_to_reset_to

    def computeState(self, dic):
        '''Compute state from data obtained in Dictonary

        Args:
            dic : a dictionary passed back by the sink of the
                  per_step_plan

        Returns:
            state: current state to be returned to OpenAI
                   typically a vector of floats.

        If the default per_step_plan is used dic will contain the
        data read back from all detectors
        '''
        raise AssertionError('Implement in derived class')
        state = None
        return state

    def computeRewardTerminal(self, d):
        '''Compute reward and terminal from state d

        Args:
            d: a dictonary containing the reuslt

        Returns:
            reward (float): The reward of the observer
            terminal (bool): Whether the observation ends the episode.

        If the default per_step_plan is used dic will contain the
        data read back from all detectors
        '''
        raise AssertionError('Implement in derived class')

        reward = None
        terminal = None
        return reward, reward

    def checkOnStart(self):
        '''

        Todo:
            What must be done here?
        '''

    #-------------------------------------------------------------------------
    # Methods expected by the OpenAI solvers
    def setup(self):
        '''Exeucte start plan and store the state

        Will read the device and handle the output dictionary to
        :meth:`storeInitialState`.

        '''
        self.state.set_setting_up()
        cmd = functools.partial(self.setup_plan, self.detectors, self.motors, 
                                self.user_args, self.user_kwargs)
        r = self._submit(cmd)
        self.storeInitialState(r)
        self.state.set_initialised()

    def close(self):
        '''What to emit to the run engine?
        '''
        self.state.set_tearing_down()
        reset_state = self.getStateToResetTo()
        cmd = functools.partial(self.teardown_plan, self.detectors, self.motors,
                                self.state_motors, reset_state,
                                self.user_args, self.user_kwargs)
        self._submit(cmd)

        # Inform bluesky that we are done ...
        self._executor.stopCommandExecution()
        self.state.set_undefined()

    def done(self):
        self._executor.stopCommandExecution()
        self.state.set_done()

    def step(self, actions):
        """Run one timestep of the environment's dynamics.

        Accepts an action and returns a tuple (observation, reward, done, info).

        Args:
            action (object): An action provided by the environment.

        Returns:
            observation (object): Agent's observation of the current environment.
            reward (float) :      Amount of reward returned after previous action.
            done (boolean):       Whether the episode has ended, in which case
                                  further step() calls will return undefined results.
            info (dict):          Contains auxiliary diagnostic information (helpful
                                  for debugging, and sometimes learning).
        """

        self.state.set_stepping()

        lm = len(self.motors)
        try:
            if lm == 1:
               # Should be float compatible
               float(actions)
               actions = [actions]

            l = len(actions)
            lm = len(self.motors)
            
            if l != lm:
                txt = (
                    f'At each step I expect {lm} = number of motors actions'
                    f' but got only {l} actions'
                    )
                raise AssertionError(txt)
        except Exception:
            self.state.set_stepping()
            self.executor.stopCommandExecution()
            raise

        cmd = functools.partial(self.per_step_plan, self.detectors, self.motors, actions,
                                self.user_args, self.user_kwargs)
        print(f'step executing command {cmd}')
        r_dic = self._submit(cmd)

        # Process result
        state = self.computeState(r_dic)
        reward, done = self.computeRewardTerminal(r_dic)
        info = {}
        if done:
            self.state.set_done()
        return state, reward, done, info

    def reset(self):
        '''

        Todo:
            The device should now what its inital state was.
            What's the bluesky equivalent to this call
        '''
        self.state.set_resetting()
        reset_state = self.getStateToResetTo()
        cmd = functools.partial(self.reset_plan, self.detectors, self.state_motors, reset_state,
                                self.user_args, self.user_kwargs)

        # Process result
        r_dic = self._submit(cmd)

        # Translate it to a state
        state = self.computeState(r_dic)
        self.state.set_initialised()
        return state

    def __enter__(self):
        """Support with-statement for the environment. """
        self.checkOnStart()
        return self

    def __exit__(self, *args):
        """Support with-statement for the environment. """
        self.close()
        # propagate exception
        return False

    def __repr__(self):
        cls_name = self.__class__.__name__
        txt = (
            f'{cls_name}('
            f'detectors={self.detectors}, motors={self.motors}'
            f' per_step_plan={self.per_step_plan},'
            f' reset_plan={self.reset_plan},'
            f' setup_plan={self.setup_plan},'
            f' teardown_plan={self.teardown_plan},'
            f' executor={self._executor},'
            f' user_args={self.user_args}'
            f' user_kwargs={self.user_kwargs}'
            ')'
        )
        return txt

    def _submit(self, cmd):
        assert(not self.state.is_failed)
        try:
            r = self.executor.submit(cmd)
        except Exception:
            self.state.set_failed()
            self._executor.stopCommandExecution()
            raise 
        return r

    @property
    def executor(self):
        assert(self._executor is not None)
        return self._executor

    @executor.setter
    def executor(self, obj):
        assert(obj is not None)
        assert(callable(obj.submit))
        assert(callable(obj.stopCommandExecution))
        self._executor = obj

    def clearLinkToExecutor(self):
        self._executor = None

