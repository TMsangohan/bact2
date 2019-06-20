import sys
sys.path.append('/opt/OPI/MachinePhysics/MachineDevelopment/mertens/github-repos/suitcase-elasticsearch')

import elasticsearch
from sshtunnel import SSHTunnelForwarder
from suitcase.elasticsearch import Serializer as ElsSerializer

host = "skylab.acc.bessy.de"
db = "StorageRing"

if False:
    from getpass import getpass
    login = getpass()
    pwd = getpass()
else:
    import os
    login = os.environ['MONGO_USER']
    pwd= os.environ['MONGO_PASS']


import logging
logger = logging.getLogger('bact2')
logger.setLevel('INFO')

class Serializer( ElsSerializer ):
    """
    """
    def __init__(self, server = None):

        self.__server = None
        
        if server is None:
            server = self.__createServer()
        self.__server = server
        super().__init__('localhost', self.__server.local_bind_port)
        
    def __createServer(self):

        logger.debug('{}: Creating server'.format(self.__class__.__name__))
        server = SSHTunnelForwarder(
	    host,
	    ssh_username=login,
	    ssh_password=pwd,
	    remote_bind_address=('0.0.0.0', 9200)
        )
        
        # START SSH TUNNEL SERVER
        server.start()
        # see https://github.com/pahaz/sshtunnel/issues/138
        # [ serv.block_on_close = False for serv in server._server_list]
        server._server_list[0].block_on_close = False
        return server
    
    
    def closeServer(self):
        server = self.__server

        logger.info('Request for closing server')
        if server is not None:
            logger.info('Closing server')
            server.close()
            server.stop()

        logger.info('Server closed')
        self.__server = None
        
    def __del__(self):
        self.closeServer()
        
