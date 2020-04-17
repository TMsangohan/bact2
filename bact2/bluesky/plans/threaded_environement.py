from bluesky import plan_stubs as bps, preprocessors as bpp
from .executor import PlanDelegatorExecutor, execute_plan_stub
from queue import Queue
from threading import Thread
import logging
import itertools

logger = logging.getLogger('bact2')


def setup_threaded_executor():
    q_cmd = Queue(maxsize=1)
    q_res = Queue(maxsize=1)

    executor = PlanDelegatorExecutor(command_queue=q_cmd, result_queue=q_res)
    return executor


def run_environement(env, partial, md=None, log=None, n_loops=1):
    '''Plan for executing environement.

    Args:
        env : a instanance of a subclass of :class:Environment
        n_loops : if negative run for ever

    This plan expects that env is used as an environement in an
    OpenAI or keras learning environment.

    Warning:
        The learning environment must be executed in an independent
        thread or process.


    Typical usage:

    ::

        executor = executor.Planexecutor(
            command_queue=Queue(maxsize=1),
            result_queue=Queue(maxsize=1),
        )

        env = Environment(detectors, motors)
        agent = SomeAgent(env)
        def run():
           agent.fit()
           return

        thread = threading.Thread(target=run)
        tread.start()
        RE(executor)
        thread.stop()
    '''


    if log is None:
        log = logger

    # 0 loops or no loops does not make sense ...
    assert(n_loops != 0)

    detectors = list(env.detectors)
    motors = list(env.motors)
    state_motors = list(env.state_motors)
    _md = {
        'detectors': [det.name for det in detectors],
        'plan_args': {
            'environent' : repr(env),
            # All arguments further down should be now in environment
            'detectors' : list(map(repr, detectors)),
            'motors' : list(map(repr, motors)),
            'state_motors' : list(map(repr, state_motors)),
            'per_step_plan' : repr(env.per_step_plan),
            'setup_plan' : repr(env.setup_plan),
            'teardown_plan' : repr(env.teardown_plan),
            'n_loops' : n_loops,
          },
        'plan_name' : 'environement_executor',
        'executor_type' : 'threaded',
        'hints' : {}
    }
    _md.update(md or {})

    clear_method = env.clearLinkToExecutor

    objects_all = (detectors + motors + state_motors)
    @bpp.stage_decorator(objects_all)
    @bpp.run_decorator(md=_md)
    def run_inner():
        executor = setup_threaded_executor()

        def run_partial(partial):
            return partial()

        try:
            env.executor = executor
            env.executor

            thread = Thread(target=run_partial, args=[partial], name='run optimiser')
            thread.start()
            log.info(f'run_environement: thread evaluating partial, executing plan')
            for cnt in itertools.count():
                if n_loops < 0 or cnt < n_loops:
                    log.info(f'run_environement: running loop {cnt}')
                    r = (yield from execute_plan_stub(executor, log=log))
        except Exception:
            log.error(f'run_environement: Failed to execute environment {env}')
            raise 
        finally:
            log.info(f'run_environement: Finishing processing  {env}')
            thread.join()
            clear_method()
        # thread.join()

        return r

    return (yield from run_inner())