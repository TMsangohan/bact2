'''Utility to sort steerers  using the info of the BESSY II EPICS name
'''
from .utils import Counter
import numpy as np
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

def provide_steerer_sort(df, steerer_name='sc_selected'):

    sel = df.loc[:, steerer_name]
    tmp = [SteererSort(*tup) for tup in zip(sel, df.index)]
    tmp.sort()
    counter = Counter()
    for t in tmp:
        t.count = counter(t.name)
    return tmp



def compute_relative_step(df, ref_current):
    dI = df.bk_dev_dI
    scale = df.bk_dev_scale_factor
    sr = scale * ref_current
    relative_step = dI / sr
    return relative_step


def add_relative_steps(df, horizontal_current, vertical_current, copy=True):
    if copy:
        df = df.copy()

    indices = (
        df.steerer_type == 'horizontal',
        df.steerer_type == 'vertical'
    )
    start_currents =(
        horizontal_current,
        vertical_current
    )
    for index, start_current in zip(indices, start_currents):
        sel  = df.loc[index, :]
        relative_step = compute_relative_step(sel,start_current)
        df.loc[index, 'relative_step'] = relative_step
    return df

def add_steerer_info(df, copy = True):
    '''
    '''
    if copy:
        df = df.copy

    st_sort = provide_steerer_sort(df)
    vals = [(st.payload, st.count,  st.type) for st in st_sort]
    vals = np.array(vals, np.object_)
    indices, count, steerer_type = vals.transpose()

    # Check that acceptable steerernames are found
    steerer_type_flagged = (steerer_type == 'h') | (steerer_type == 'v')
    assert((steerer_type_flagged == True).all())

    # I prefer names that are better to read
    steerer_type = np.where(steerer_type == 'h', 'horizontal', 'vertical')

    res = np.array([count, steerer_type], np.object_)
    df.loc[indices, ['steerer_pos', 'steerer_type']] = res.transpose()
    return df