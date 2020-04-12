import logging
logging.basicConfig(level='INFO')

log = logging.getLogger('bact2')

def main():
    from xmlrpc.client import ServerProxy
    

    class MyProxy(ServerProxy):
        def seed(self, *args, **kwargs):
            seed = super().seed(*args, **kwargs)
            r = int(seed)
            return r

    with ServerProxy("http://localhost:8000/", verbose=True) as proxy:
        try:
            proxy.seed()
            log.info('\nSetup start\n')
            proxy.setup()
            log.info('\nSetup succeded\n')
            proxy.reset()
            log.info('\nReset succeded\n')
            r = proxy.step(.2)
            log.info(f'\nStep succeded {r}\n')
            proxy.done()
            #log.info('\nDone succeded\n')
        finally:
            log.info('Closing Proxy')
        #    proxy.close()

if __name__ == '__main__':
    main()
