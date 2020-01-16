from ...pandas.dataframe import df_aggregate as dfg
import pandas as pd
import numpy as np


def calculate_bpm_one_corr(df_sel, coor=None):
    assert(coor is not None)
    dI = df_sel.sc_sel_dev_setpoint - df_sel.bk_dev_current_offset
    if coor == 'x':
        bpm = df_sel.bpm_waveform_x_pos
    elif coor == 'y':
        bpm = df_sel.bpm_waveform_y_pos
    else:
        raise AssertionError('coor {} unknown'.format(coor))

    bpm = np.array(bpm.values.tolist(), np.float_)
    # Critical for rcond determination
    dI = np.array(dI.values, np.float_)
    gain, offset = np.polyfit(dI, bpm, 1)
    res = {'gain': gain, 'offset': offset}
    return res


def calculate_bpm(df_sel):
    result = {}
    for coor in ('x', 'y'):
        r = calculate_bpm_one_corr(df_sel, coor)
        result[coor] = r
    return result


def calc_bpm_gains(df, column_name='sc_selected'):

    tdf = dfg.df_with_vectors_mean(df, column_name)
    columns = ['bpm_ox', 'bpm_oy', 'bpm_gx', 'bpm_gy']

    ncols = set(list(tdf.columns) + columns)
    df_ref = pd.DataFrame(index=tdf.index, columns=ncols, dtype=np.object_)

    group = df.groupby(by=column_name)
    for key, index in group.groups.items():
        df_sel = df.loc[index, :]
        result = calculate_bpm(df_sel)
        df_ref.loc[key, 'bpm_gx'] = result['x']['gain']
        df_ref.loc[key, 'bpm_gy'] = result['y']['gain']
        df_ref.loc[key, 'bpm_ox'] = result['x']['offset']
        df_ref.loc[key, 'bpm_oy'] = result['y']['offset']

    # Why has to be done afterwards ....
    for col in tdf.columns:
        if col not in columns:
            df_ref.loc[:, col] = tdf.loc[:, col]

    return df_ref


def _calc_bpm_reference(dI, offset, gain):
    ref_val = offset[np.newaxis, :] + gain[np.newaxis, :] * dI[:, np.newaxis]
    return ref_val


def calc_bpm_diff(df, ref, column_name='sc_selected'):
    '''estimate of the non linearity
    '''
    ndf = pd.DataFrame(index=df.index, columns=df.columns, dtype=np.object_)

    assert(ndf.shape == df.shape)
    ref_cols = ['bpm_x_ref', 'bpm_y_ref']


    grp = df.groupby(by=column_name)
    for key, index in grp.groups.items():
        t_ref = ref.loc[key, :]
        ox = t_ref.loc['bpm_ox']
        gx = t_ref.loc['bpm_gx']
        oy = t_ref.loc['bpm_oy']
        gy = t_ref.loc['bpm_gy']

        # Now reference for each point
        sel = df.loc[index, :]
        # print(sel)
        I = sel.sc_sel_dev_setpoint
        I_ref = sel.bk_dev_current_offset
        dI = I - I_ref

        x_ref = _calc_bpm_reference(dI, ox, gx)
        y_ref = _calc_bpm_reference(dI, oy, gy)

        x_ref_d = [row for row in x_ref]
        y_ref_d = [row for row in y_ref]
        x_r_s = pd.Series(index=index, data=x_ref_d, dtype=np.object_)
        y_r_s = pd.Series(index=index, data=y_ref_d, dtype=np.object_)

        ndf.loc[index, 'bpm_x_ref'] = x_r_s
        ndf.loc[index, 'bpm_y_ref'] = y_r_s

        # for i in range(len(index)):
        #    idx = index[i]
        #    ndf.loc[idx, 'bpm_x_ref'] = x_ref[i]
        #    ndf.loc[idx, 'bpm_y_ref'] = y_ref[i]

    for col in df.columns:
        if col not in ref_cols:
            ndf.loc[:, col] = df.loc[:, col]
    return ndf
