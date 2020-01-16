'''utilities for aggregating dataframes containing vectors

Main entry points:
   * :func:`df_with_vectors_mean`
   * :func:`df_with_vectors_aggregate`
'''
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger('bact2')


def time_vector_mean(vec, df=None):
    '''Calculate the average time for a sequence of datetime values


    Args:
        vec : a vector of values of type datetime64

    Returns:
        the datetime64 value corresponding to the mean date

    datetime does not allow adding two values. Thus any mean value
    calculation fails.

    This implementation uses the first element as reference and
    calculates the mean value of all dt's.
    '''

    ref = vec[0]
    dt = vec - ref
    return ref + dt.mean()


def time_series_mean(t_series, df=None):
    '''Calculate the mean value of a time series

    Used as possible callback for :func:`df_with_vectors_aggregate`
    '''
    return time_vector_mean(t_series.values)


def vectors_mean(t_vecs, df=None):
    '''Calculate the mean value for each vector

    Used as possible callback for :func:`df_with_vectors_aggregate`
    '''
    return np.mean(t_vecs, axis=0)

def vectors_mean_skip_first(t_vecs, df=None):
    assert(df is not None)

    t_time = df.time
    idx = t_time.argsort().min()
    if idx != 0:
        raise AssertionError('first measurement was not the first entry')
    reduced = t_vecs[1:]
    return np.mean(reduced, axis=0)


def vector_strings_same_value(t_vecs, df=None):
    '''return the first vector if all following vectors are identical

    Used for processing strings by :func:`df_with_vectors_aggregate`
    '''

    test_vector = t_vecs[0]
    test = False

    for check in t_vecs[1:]:
        flag = check == test_vector
        flag = np.asarray(flag)
        test = flag.all()
        if not test:
            return None

    return test_vector


def vector_aggregate_check_keywords(**kws):

    func_for_vecs = kws.pop('func_for_vecs', None)
    assert(func_for_vecs is not None)
    assert(callable(func_for_vecs))

    func_for_time = kws.pop('func_for_time', None)

    if func_for_time is not None:
        assert(callable(func_for_time))

    error_msg_f = kws.pop('error_msg_f', None)

    assert(error_msg_f is not None)
    assert(callable(error_msg_f))


def _vector_aggregate(t_data, func_for_vecs=None, func_for_time=None,
                      error_msg_f=None, column_name=None, l_index=None,
                      df=None):

    try:
        return func_for_vecs(t_data.values, df=df)
    except Exception:
        logger.debug(error_msg_f() + '; first try')

    # Aggregation calculation of datetime values require
    # a different treatment as numerical values
    if t_data.dtype in [np.datetime64, np.dtype('<M8[ns]')]:
        fmt = ('Special treatment for column "{}" containing values'
               ' of type datetime64')
        logger.debug(fmt.format(column_name))
        if func_for_time:
            return func_for_time(t_data, df=df)
        else:
            return None

    values = t_data.values
    # Arrays of strings are stored in an object structure
    # Search for these string arrays
    lv = len(values)
    if lv == l_index:
        first = values[0]
        first = np.asarray(first)
        dtype = None
        try:
            dtype = first.dtype
        except AttributeError:
            fmt = 'Dtype could not be determined for first {}'
            logger.debug(fmt.format(first))

        if dtype is not None and np.issubsctype(dtype, str):
            fmt = "found strings in column {} processing as strings!"
            logger.debug(fmt.format(column_name))
            return vector_strings_same_value(values, df=df)

    fmt = 'Column {} len (values) = {} len (index) = {} '
    logger.debug(fmt.format(column_name, lv, l_index))

    # All columns should now be treated
    txt = error_msg_f()
    logger.debug(txt)
    raise AssertionError(txt)


def vector_aggregate(t_data, func_for_vecs=None, func_for_time=None,
                     error_msg_f=None, column_name=None):

    kws = {
        'func_for_vecs': func_for_vecs,
        'func_for_time': func_for_time,
        'error_msg_f': error_msg_f,
        'column_name': column_name
    }
    vector_aggregate_check_keywords(**kws)
    return _vector_aggregate(t_data, **kws)


def df_with_vectors_aggregate(df, group, grouped_df, func_for_vecs,
                              func_for_time=None):
    '''Aggregate a data frame with its vectors

    Args:
        df :           the original df
        group :        a group object (used to index into df)
        grouped_df:    the dataframe containing the already grouped values
        func_for_vecs: function processing aggregation for vectors containing
                       numerical values
        func_for_time: function processing aggregation for vectors containing
                       np.datetime64 values

    Returns:
        a dataframe containing aggregation of the scalars and vectors
    '''

    def error_msg_f_fake():
        '''Once more a lion in Cairo'''
        raise AssertionError('This function should not be called!')

    kws = {
        'func_for_vecs': func_for_vecs,
        'func_for_time': func_for_time,
        'error_msg_f': error_msg_f_fake,
    }
    vector_aggregate_check_keywords(**kws)

    missing_cols = set(df.columns) - set(grouped_df.columns)
    logger.debug('Columns treated additionally {}'.format(missing_cols))

    #
    # I do not manage to use reindex or similar. Thus I recreate a
    # new dataframe.
    #
    # Copy the ones already existing
    columns = list(grouped_df.columns) + list(missing_cols)
    ndf = pd.DataFrame(index=grouped_df.index, columns=columns)
    for col in grouped_df.columns:
        ndf.loc[:, col] = grouped_df.loc[:, col]

    # Special treatment for vector like frames
    for target_index, index in group.groups.items():
        for col in missing_cols:
            df_sel = df.loc[index, :]
            t_data = df.loc[index, col]

            def errmsg():
                nonlocal col, t_data

                values = np.asarray(t_data.values)
                rv = values.ravel()
                try:
                    dtype = rv[0].dtype
                except Exception:
                    dtype = 'dtype could not be determined'
                tup = (col, t_data.dtype, t_data.shape, dtype)
                fmt = ('Vector conversion failed for column' +
                       ' {} (type {}  shape {}) first element type {}')
                txt = fmt.format(*tup)
                return txt

            kws['error_msg_f'] = errmsg
            l_index = len(index)
            elem = _vector_aggregate(t_data, column_name=col, l_index=l_index,
                                     df=df_sel, **kws)
            if elem is not None:
                # Using index in the first column did not work for me
                ndf.loc[:, col].at[target_index] = elem

    return ndf


def df_with_vectors_mean(df, column_name):
    '''

    aggregate a data frame containing bpm data
    '''
    grp = df.groupby(column_name)
    tdf = grp.mean()

    return df_with_vectors_aggregate(df, grp, tdf, vectors_mean,
                                     func_for_time=time_series_mean)


def df_with_vectors_mean_skip_first(df, column_name='measurement'):
    '''Calculate the mean by skipping the first measurement
    '''
    grp = df.groupby(by=column_name)
    tdf = grp.mean()

    return df_with_vectors_aggregate(df, grp, tdf, vectors_mean_skip_first)

def df_vectors_convert(df, copy = True):
    '''Convert objects to vectors if possible

    JSON export e.g. exports objects as lists. These require to be
    converted back for further processing.

    Best practise: call :meth:`df.infer_objects` first

    Todo:
        Check if array strings require further processing
    '''
    if copy:
        df = df.copy()

    rows = range(df.shape[0])
    for col in df.columns:
        t_col = df.loc[:, col]
        dtype = t_col.dtype
        if dtype != np.object_:
            continue

        # try to convert the first object in the column
        obj = t_col.iat[0]
        test = np.array(obj)
        test_d = test.dtype

        fmt = 'column {} test dtype {} object dtype {}'
        txt = fmt.format(col, dtype, test_d)
        logger.debug(txt)

        if test_d not in [np.float64, np.int64]:
            continue

        # Array type known, lets convert it
        as_list = t_col.values.tolist()

        # nd = pd.Series(index=df.index, data=as_list, dtype=np.object_)
        # df.loc[:, col] = nd
        converted_array = np.array(as_list, test_d)
        for row in rows:
            df.loc[:, col].iat[row] = converted_array[row]

    return df
