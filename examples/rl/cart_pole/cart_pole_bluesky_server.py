
def main():
    import logging
    logging.basicConfig(level='INFO')

    from bact2.bluesky.plans.threaded_environement import run_environement

    from bluesky import RunEngine
    from cart_pole_device import CartPole
    from cart_pole_environment import CartPoleEnv

    import xmlrpc.server
    import functools
    import numpy
    import zmq

    logger = logging.getLogger('bact2')

    cart_pole = CartPole(name = 'cp')

    RE = RunEngine({})
    RE.log.setLevel('INFO')
    cart_pole.log = RE.log

    class TheEnv(CartPoleEnv):
        def seed(self, *args, **kwargs):
            seed = super().seed(*args, **kwargs)
            assert(len(seed) == 1)
            seed = seed[0]
            r = f'{seed:d}'
            return r

        def reset(self, *args, **kwargs):
            r = super().reset(*args, **kwargs)
            r = [float(x) for x in r]
            self.log.error(f'Reset returned {r}')
            return r

        def step(self, *args, **kwargs):
            r = super().step(*args, **kwargs)
            state, action, done, info = r
            self.log.error(f'step returned unconverted {r}')
            state = [float(x) for x in state]
            r = state, action, done, info
            self.log.error(f'step returned {r}')
            return r

        def close(self, *args, **kwargs):
            r = super().close(*args, **kwargs)
            self.log.error(f'close returned {r}')
            return r

    stm = [cart_pole.x, cart_pole.x_dot, cart_pole.theta, cart_pole.theta_dot]
    cpst = TheEnv(detectors=[cart_pole], motors=[cart_pole], 
    state_motors=stm, log=RE.log)

    def run_test(env, *, log=None):
        from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer
        # Restrict to a particular path.
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)

        with SimpleXMLRPCServer(('localhost', 8000),
                                #requestHandler=RequestHandler
                                ) as server:
            env.server = server
            server.register_introspection_functions()
            server.register_instance(env)
            server.allow_none = True
    
            log.info('XML Server running')
            # Run the server's main loop
            server.serve_forever()
        log.info('XML Server stopped')

    partial = functools.partial(run_test, cpst, log=RE.log)

    RE.log.info('Handling execution to bluesky')
    RE(run_environement(cpst, partial, log=RE.log, n_loops=-1))
    RE.log.info('Bluesky operation finished')

if __name__ == '__main__':
    main()



