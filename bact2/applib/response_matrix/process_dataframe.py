'''Add extra information to the bpm dataframe

'''
from importlib import reload
from bact2.applib.utils import steerer as st_u, utils as m_u
import bact2.pandas.dataframe.df_aggregate as dfg
import pandas as pd
import numpy as np

reload(st_u)
reload(m_u)
reload(dfg)


def round_float_values(values, rounding_scale=1e6):
    values = np.asarray(values)
    nvals = values * rounding_scale
    nvals = nvals.astype(np.int_)
    nvals = nvals / rounding_scale
    return nvals


cols_to_process = [
    'time',
    'sc_selected',
    'bpm_x_ref', 'bpm_y_ref',
    'bpm_x_diff', 'bpm_y_diff',
    'bpm_x_ref2', 'bpm_y_ref2',
    'bpm_x_diff2', 'bpm_y_diff2',
    'bk_dev_mode',
    'steerer_mode',
    'steerer_pos',
    'measurement',
    'I_rounded',
    'bk_dev_dI', 'bk_dev_scale_factor', 'bk_dev_current_offset',
    'sc_sel_dev_setpoint', 'sc_sel_dev_readback',
    'ramp_index',
    'bpm_waveform_x_pos', 'bpm_waveform_y_pos',
    'bpm_waveform_ds',
    'dt',
    'bpm_x_scale', 'bpm_y_scale',
    'steerer_type'
]


def provide_steerer_sort(df):
    tmp = [st_u.SteererSort(*tup) for tup in zip(df.sc_selected, df.index)]
    tmp.sort()
    counter = m_u.Counter()
    for t in tmp:
        t.count = counter(t.name)
    return tmp


def prepare_dataframe(df, columns_to_process=None):
    if columns_to_process is None:
        columns_to_process = cols_to_process

    df = df.reindex(columns=columns_to_process, index=df.index)
    df.loc[:, 'I_rounded'] = round_float_values(df.sc_sel_dev_setpoint)
    df.loc[:, 'measurement'] = -1
    df.loc[:, 'steerer_pos'] = -1
    df.loc[:, 'return amp_index'] = -1
    return df


def add_measurement_counts(df, copy=True):
    '''

    Todo:
       check if the addional copy is required
    '''
    if copy:
        df = df.copy()

    tt = m_u.add_measurement_counts(df, copy=copy)
    tt.loc[:, 'measurement'] = pd.to_numeric(tt.measurement)
    return tt


def add_steerer_info(df, copy=True):

    if copy:
        df = df.copy()

    st_sort = provide_steerer_sort(df)
    for st in st_sort:
        df.loc[st.payload, 'steerer_pos'] = int(st.count)
    if st.type == 'h':
        df.loc[st.payload, 'steerer_type'] = 'horizontal'
    elif st.type == 'v':
        df.loc[st.payload, 'steerer_type'] = 'vertical'
    else:
        fmt = 'steerer of type {} (name {}) unknwon'
        raise AssertionError(fmt.format(st.type, st.name))


def add_steerer_scale(df, column_name='sc_selected', copy=True):
    if copy:
        df = df.copy()

    df.bpm_x_diff = df.bpm_waveform_x_pos - df.bpm_x_ref
    df.bpm_y_diff = df.bpm_waveform_y_pos - df.bpm_y_ref

    grp = df.groupby(by='sc_selected')
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


def get_a_name(tt):
    table_agg = dfg.df_with_vectors_mean_skip_first(tt.infer_objects())
    assert(tt.shape[0]/table_agg.shape[0]==3)



    table_meas = table_agg.loc[table_agg.bk_dev_mode == 'store_data'].infer_objects()
    table_meas = m_u.add_measurement_index(table_meas)
    meas_ref = bd.calc_bpm_gains(table_meas)#.infer_objects()
    table_meas_w_ref = bd.calc_bpm_diff(table_meas, meas_ref)

    table_meas_w_ref = add_steerer_scale(table_meas_w_ref)



class ProcessedBPMData:
    def __init__(self, df, columns_to_process=None):

        # Check with ipython notebook if intermediate steps are appropriate
        df = prepare_dataframe(df, columns_to_process=columns_to_process)
        df = add_measurement_counts(df, copy=False)
        df = add_steerer_info(df, copy=False)

        # Che
        df = add_steerer_scale(df, copy=False)

        self.df = df

#    @property
#    def agg(self):
