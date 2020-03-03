import logging
import numpy as np

logger = logging.getLogger('bact2')

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


def add_measurement_count_inner(df, grp, counter,
                                mode_column=None, count_column=None):
    '''

    Todo:
       Check if it is still used..
    '''
    assert(mode_column is not None)
    assert(count_column is not None)
    for mode, mi in grp.groups.items():
        steerer_meas_t = df.loc[mi, :]

        # New mode new count ... better that way
        for idx in steerer_meas_t.index:
            current = steerer_meas_t.I_rounded[idx]
            df.loc[idx, count_column] = counter(current)


def add_measurement_counts_progressive_slow(df, columns=None, count_column=None,
                                        copy=True, counter=None):
    '''

    Separate measurement by columns....

    Be aware:
       this uses grp. If you need to flag every change you need a different function
    '''

    assert(columns is not None)
    if columns is None:
        columns = ['sc_selected', 'bk_dev_mode', 'I_rounded']
        # steerer_column = 'sc_selected',
        # mode_column = 'bk_dev_mode',

    assert(type(columns) == type([]))
    assert(count_column is not None)

    if copy:
        df = df.copy()

    if counter is None:
        counter = Counter()

    for idx in df.index:
        row_sel = df.loc[idx, columns]
        indicator_for_change = tuple(row_sel.values)
        val = counter(indicator_for_change)
        df.loc[idx, count_column] = val
        txt = (
            f'progressive counting columns {columns}:'
            f' index: {idx} counter {val}'
        )
        logger.debug(txt)

    return df


def measurement_counts(t_array):
    '''increase measurement count each time a value changes in the riw
    '''
    # Compare folllowing line to this line
    t_array = np.atleast_2d(t_array)
    if len(t_array.shape) != 2:
        raise AssertionError('Only implemented for matrix')

    flags = (t_array[1:] == t_array[:-1])
    # Flag the changes
    flags = np.logical_not(flags)
    # flag the changeed line
    row_with_change = flags.any(axis=1)
    counter = row_with_change.cumsum()
    return counter


def add_measurement_counts_progressive(df, columns=None, count_column=None,
                                           copy=True, counter=None):
    '''

    Separate measurement by column values ... numpy
    '''

    assert(columns is not None)
    assert(type(columns) == type([]))
    assert(count_column is not None)

    if copy:
        df = df.copy()

    df_sel = df.loc[:, columns]
    np_sel = df_sel.values

    counter = measurement_counts(np_sel)

    df.loc[:, count_column] = 1
    indices = df.index[1:]
    df.loc[indices, count_column] = counter

    return df


def add_measurement_index(df, column=None):
    df = df.copy()

    assert(column is not None)

    if column is None:
        column='sc_selected'
    logger.info(f'Adding measurement index based on column {column}')
    grp = df.groupby(column)

    check = None
    cnt = 0
    for name, indices in grp.groups.items():
        cnt += 1
        l_index = len(indices)
        if check is None:
            check = l_index
        if check != l_index:
            txt = (
                f'Adding measurement index for {name}: expected a group of {check}'
                f' but found {l_index} elements: error occured in round {cnt}'
            )
            logger.error(txt)
            # raise AssertionError(txt)

        n_measurement = range(l_index)
        # print(name, indices)
        df.loc[indices, 'ramp_index'] = n_measurement
    return df


def count_measurements_broken(df, columns):
    '''
    Todo:
        fix calling code to use  add_measurement_counts_progressive instead
    '''
    all_flags = None
    for col in columns:
        sel = df.loc[:, col].values
        flags = sel[1:] != sel[:-1]
        if all_flags is None:
            all_flags = flags
        else:
            all_flags = all_flags | flags
    return flags


def add_measurement_counts(df, columns=None, count_column='measurement',
                            copy=True):
    '''

    Todo:
        Fix code that relies the the columns are defined
    '''
    if copy:
        df = df.copy()

    assert(columns is not None)

    if columns is None:
        columns = ['sc_selected', 'bk_dev_mode', 'I_rounded']

    logger.info(f'Adding measurement count based on columns {columns}')

    try:
        all_flags = count_measurements(df, columns)
    except Exception:
        logger.error(f'Failed while processings columns {columns}')
        raise
    # return all_flags
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
