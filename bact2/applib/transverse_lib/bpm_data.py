from ...pandas.dataframe import df_aggregate as dfg
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger('bact2')

def calculated_indep_relative_value(df, indep_column=None, indep_ref_column=None):
    assert(indep_column is not None)

    dI = df.loc[:, indep_column]
    if indep_ref_column is None:
        return dI

    # for loco this is bk_dev_current_offset
    offset = df.loc[:, indep_ref_column]

    try:
        # for loco this is sc_sel_dev_setpoint
        dI = dI - offset
    except Exception:
        txt = (
            f'indep calculation failed using'
            f' column {indep_column} for the values'
            f' and colum {indep_ref_column} as offsets'
            f' indep values {dI}'
        )
        logger.error(txt)
        raise

    return dI


def calculate_bpm_one_corr(df_sel, coor=None,
                           indep_column=None, indep_ref_column=None):

    assert(coor is not None)

    dI = calculated_indep_relative_value(df_sel, indep_column=indep_column,
                                         indep_ref_column=indep_ref_column)
    if coor == 'x':
        bpm = df_sel.bpm_waveform_x_pos
    elif coor == 'y':
        bpm = df_sel.bpm_waveform_y_pos
    else:
        raise AssertionError('coor {} unknown'.format(coor))

    bpm = np.array(bpm.values.tolist(), np.float_)

    # Critical for rcond determination
    dI = np.array(dI.values, np.float_)

    # Are sufficient data available?
    n_points = dI.shape[0]

    m_measurements = bpm.shape[1]

    fill_vals = np.zeros((m_measurements,), np.float_) + np.nan
    offset = gain = fill_vals
    curve = slope = intercept = fill_vals

    if n_points < 2:
        logger.info(f'Can not compute any fit for dI {dI} insufficient points')
    elif n_points == 2:
        txt = (
            f'Can only compute linear fit for dI {dI}:'
            f' insufficient points for cubic fit: {n_points} ==2'
        )
        logger.info(txt)

    if n_points >= 2:
        gain, offset = np.polyfit(dI, bpm, 1)
    elif n_points >= 3:
        curve, slope, intercept = np.polyfit(dI, bpm, 2)

    res = {
        'gain': gain, 'offset': offset,
        'curve': curve, 'slope': slope, 'intercept': intercept
    }

    return res


def calculate_bpm(df_sel, **kws):
    result = {}
    for coor in ('x', 'y'):
        r = calculate_bpm_one_corr(df_sel, coor, **kws)
        result[coor] = r
    return result


def calc_bpm_gains(df, column_name=None, indep_column=None,
                   indep_ref_column=None):
    '''

    Todo:
        make indep_column and indep_ref_column None by default
    '''

    assert(column_name is not None)
    # loco script used it already in this manner
    # let's save it for testing
    if column_name is None:
        column_name = 'sc_selected'

    tdf = dfg.df_with_vectors_mean(df, column_name)
    columns = [
        'bpm_ox', 'bpm_oy', 'bpm_gx', 'bpm_gy',
        'bpm_p2_x_i', 'bpm_p2_x_s', 'bpm_p2_x_c',
        'bpm_p2_y_i', 'bpm_p2_y_s', 'bpm_p2_y_c',
    ]

    ncols = set(list(tdf.columns) + columns)
    df_ref = pd.DataFrame(index=tdf.index, columns=ncols, dtype=np.object_)

    group = df.groupby(by=column_name)
    for key, index in group.groups.items():
        df_sel = df.loc[index, :]

        logger.debug(
            f'grouped by {column_name}:'
            f' key {key} found {df_sel.shape[0]} entries'
        )

        result = calculate_bpm(df_sel, indep_column=indep_column,
                               indep_ref_column=indep_ref_column)
        df_ref.loc[key, 'bpm_gx'] = result['x']['gain']
        df_ref.loc[key, 'bpm_gy'] = result['y']['gain']
        df_ref.loc[key, 'bpm_ox'] = result['x']['offset']
        df_ref.loc[key, 'bpm_oy'] = result['y']['offset']

        df_ref.loc[key, 'bpm_p2_x_i'] = result['x']['intercept']
        df_ref.loc[key, 'bpm_p2_x_s'] = result['x']['slope']
        df_ref.loc[key, 'bpm_p2_x_c'] = result['x']['curve']

        df_ref.loc[key, 'bpm_p2_y_i'] = result['y']['intercept']
        df_ref.loc[key, 'bpm_p2_y_s'] = result['y']['slope']
        df_ref.loc[key, 'bpm_p2_y_c'] = result['y']['curve']

    # Why has to be done afterwards ....
    for col in tdf.columns:
        if col not in columns:
            df_ref.loc[:, col] = tdf.loc[:, col]

    return df_ref


def _calc_bpm_reference(dI, offset, gain):
    ref_val = offset[np.newaxis, :] + gain[np.newaxis, :] * dI[:, np.newaxis]
    return ref_val


def _calc_bpm_reference_p2(dI, intercept, slope, curve):
    dI_mat    = dI[:, np.newaxis]

    intc_mat  = intercept[np.newaxis, :]
    slope_mat = slope[np.newaxis, :]
    curve_mat = curve[np.newaxis, :]

    ref_val = intc_mat + dI_mat * (slope_mat + curve_mat * dI_mat)
    return ref_val


def calc_bpm_ref(df, ref, column_name=None,
                 indep_column=None, indep_ref_column=None):
    '''reference data from fit data
    '''

    assert(column_name is not None)

    if column_name is None:
        column_name = 'sc_selected'

    ndf = pd.DataFrame(index=df.index, columns=df.columns, dtype=np.object_)

    assert(ndf.shape == df.shape)
    ref_cols = [
        'bpm_x_ref', 'bpm_y_ref',
        'bpm_x_ref2', 'bpm_y_ref2',
    ]

    grp = df.groupby(by=column_name)
    for key, index in grp.groups.items():
        t_ref = ref.loc[key, :]

        # Now reference for each point
        sel = df.loc[index, :]
        # print(sel)

        logger.info(f'grouped by {column_name}: key {key} found {sel.shape[0]} entries ')
        dI = calculated_indep_relative_value(sel, indep_column=indep_column,
                                             indep_ref_column=indep_ref_column)

        for coor in ('x', 'y'):
            offset = t_ref.loc[f'bpm_o{coor}']
            gain   = t_ref.loc[f'bpm_g{coor}']

            ints  = t_ref.loc[f'bpm_p2_{coor}_i']
            slope = t_ref.loc[f'bpm_p2_{coor}_s']
            curve = t_ref.loc[f'bpm_p2_{coor}_c']

            ref_val = _calc_bpm_reference(dI, offset, gain)
            ref_val2 = _calc_bpm_reference_p2(dI, ints, slope, curve)

            ref_d = [row for row in ref_val]
            ref_d2 = [row for row in ref_val2]
            r_s = pd.Series(index=index,  data=ref_d, dtype=np.object_)
            r_s2 = pd.Series(index=index, data=ref_d2, dtype=np.object_)

            ndf.loc[index, f'bpm_{coor}_ref'] = r_s
            ndf.loc[index, f'bpm_{coor}_ref2'] = r_s2

    for col in df.columns:
        if col not in ref_cols:
            ndf.loc[:, col] = df.loc[:, col]
    return ndf


def add_bpm_deviation_from_fit(df, copy=True):
    if copy:
        df = df.copy()

    df.bpm_x_diff = df.bpm_waveform_x_pos - df.bpm_x_ref
    df.bpm_y_diff = df.bpm_waveform_y_pos - df.bpm_y_ref

    df.bpm_x_diff2 = df.bpm_waveform_x_pos - df.bpm_x_ref2
    df.bpm_y_diff2 = df.bpm_waveform_y_pos - df.bpm_y_ref2

    return df


def add_bpm_scale(df, column_name=None, copy=True):

    if copy:
        df = df.copy()

    assert(column_name is not None)
    if column_name is None:
        column_name = 'sc_selected'

    grp = df.groupby(by=column_name)
    for steerer_name, index in grp.groups.items():
        sel = df.loc[index, :]
        sel_ri = sel.loc[sel.ramp_index == 4, :]
        assert(sel_ri.shape[0] == 1)

        # scale for the x factor
        s_x = sel_ri.bpm_waveform_x_pos.iat[0]
        # scale for the y factor
        s_y = sel_ri.bpm_waveform_y_pos.iat[0]

        # What are the s_x and s_y scale?
        # needs to be documented
        li = len(index)
        ss_x = pd.Series(index=index, data=[s_x] * li, dtype=np.object_)
        ss_y = pd.Series(index=index, data=[s_y] * li, dtype=np.object_)

        df.loc[index, 'bpm_x_scale'] = ss_x
        df.loc[index, 'bpm_y_scale'] = ss_y

    return df
