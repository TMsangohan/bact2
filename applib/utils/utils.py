class Counter:
    '''Faclitates counting measurements

    Todo:
        Check if implementation available
    '''
    def __init__(self):
        self._old_value = None
        self._counter = 0

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

    # def __del__(self):
    #    # txt = 'Last count was {}'.format(self._counter)
    #    # print(txt)
    #    pass


def add_measurement_count(df, grp, counter,
                          mode_column=None, count_column=None):
    '''
    '''
    assert(mode_column is not None)
    assert(count_column is not None)
    for mode, mi in grp.groups.items():
        steerer_meas_t = df.loc[mi, :]

        # New mode new count ... better that way
        for idx in steerer_meas_t.index:
            current = steerer_meas_t.I_rounded[idx]
            df.loc[idx, count_column] = counter(current)

def add_measurement_counts_old(df, steerer_column='sc_selected',
                           mode_column='bk_dev_mode', copy=True):
    '''

    Separate measurement
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
        add_measurement_count(df, steerer_grp, counter,
                              mode_column=mode_column,
                              count_column='measurement')

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

def count_measurements(df, columns):
    all_flags = None
    for col in columns:
        sel = df.loc[:, col].values
        flags = sel[1:] != sel[:-1]
        if all_flags is None:
            all_flags = flags
        else:
            all_flags = all_flags | flags
    return flags

def add_measurement_counts(df, columns=['sc_selected', 'bk_dev_mode', 'I_rounded'],
                           count_column = 'measurement',
                           copy=True):
    
    if copy:
        df = df.copy()

    all_flags = count_measurements(df, columns)
    #return all_flags
    measurement_index = all_flags.cumsum()
    df.loc[:, count_column].values[0] = 0
    df.loc[:, count_column].values[1:] = measurement_index
    return df


def round_float_values(values, rounding_scale=1e6):
    import numpy as np
    values = np.asarray(values)
    nvals = values * rounding_scale
    nvals = nvals.astype(np.int_)
    nvals = nvals / rounding_scale
    return nvals