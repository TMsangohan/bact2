'''Utility to sort steerers  using the info of the BESSY II EPICS name
'''

import logging
logger = logging.getLogger('bact2')


class SteererInfo:
    '''Steerer info derived from steerer name
    '''
    __slots__ = ['type', 'sector', 'straight', 'name', 'number']

    def __init__(self, name):
        self.type = None
        self.sector = None
        self.straight = None
        self.number = None
        try:
            self.splitName(name)
        except Exception:
            txt = 'Splitting up steerer name {} failed'.format(name)
            logger.error(txt)
            raise
        self.name = name

    def splitName(self, name):
        assert(name[-1] == 'r')
        self.sector = int(name[-2])
        straight = name[-3]
        assert(straight in ['d', 't'])
        self.straight = straight

        t_type = name[0]
        assert(t_type in ['h', 'v'])
        self.type = t_type

        assert(name[1] == 's')
        self.number = int(name[2])

        assert(name[3] == 'p')

    def __eq__(self, other):
        return self.name == other.name

    def __gt__(self, other):

        if self.type != other.type:
            return self.type > other.type

        if self.number != other.number:
            return self.number > other.number

        if self.straight != other.straight:
            return self.straight > other.straight

        if self.sector != other.sector:
            return self.sector > other.sector

        return self.name > other.name

    def __repr__(self):
        fmt = '{}({})'
        txt = fmt.format(self.__class__.__name__, self.name)
        return txt


class SteererSort(SteererInfo):
    '''Utility for sorting steerers by name with a payload
    '''
    def __init__(self, name, payload):
        super().__init__(name)
        self.payload = payload
        self.count = None

    def __repr__(self):
        fmt = '{}({}, {} = {})'
        txt = fmt.format(self.__class__.__name__,
                         self.name, self.payload, self.count)
        return txt
