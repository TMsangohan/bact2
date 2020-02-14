import logging

logger = logging.getLogger('bact2')

class Counter:
    '''Faclitates counting measurements

    Every time it recieves a new value it
    will increase its internal count status

    Todo:
        Check if implementation available
    '''
    def __init__(self):
        self._old_value = None
        self._counter = 0

    # not used nor tested
    # @property
    # def counter(self):
    #    return self._counter

    def stepCounter(self):
        self._counter += 1

    def __call__(self, value):
        assert(value is not None)
        if value != self._old_value:
            self.stepCounter()
            self._old_value = value
        return self._counter

    def __del__(self):
        txt = 'Last count was {}'.format(self._counter)
        logger.debug(txt)


def _add_measurement_count(df, grp, counter, count_column=None):
    '''adds a measurement count to each column
    '''
    assert(count_column is not None)
    for mode, mi in grp.groups.items():
        df_inner = df.loc[mi, :]

        # New mode new count ... better that way
        for idx in df_inner.index:
            current = df_inner.I_rounded[idx]
            df.loc[idx, count_column] = counter(current)

def add_measurement_counts(df, steerer_column='sc_selected',
                           mode_column='bk_dev_mode',
                           count_column='measurement',
                           copy=True):
    '''Add a  consecutive number count to each new measurement

    Todo:
       Allow an abritrary number of distingquishing columns
    '''
    assert(steerer_column is not None)
    assert(mode_column is not None)

    if copy:
        df = df.copy()

    counter = Counter()
    grp = df.groupby(by=steerer_column)

    for name, indices in grp.groups.items():
        steerer_t = df.loc[indices, :]
        steerer_grp = steerer_t.groupby(by=steerer_column)
        _add_measurement_count(df, steerer_grp, counter,
                               count_column=count_column)
        # Just in case .... a bit paranoic perhaps
        counter.stepCounter()
    return df


def add_measurement_index(df):
    df = df.copy()
    grp = df.groupby('sc_selected')

    check = None
    for name, indices in grp.groups.items():
        l_index = len(indices)
        if check is None:
            check = l_index
        assert(check == l_index)
        n_measurement = range(l_index)
        # print(name, indices)
        df.loc[indices, 'ramp_index'] = n_measurement
    return df
