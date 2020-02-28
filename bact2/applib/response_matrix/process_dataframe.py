'''Add extra information to the bpm dataframe

'''
import logging
from importlib import reload
from ..utils import steerer as st_u, utils as m_u
from . import bpm_data
from ...pandas.dataframe import df_aggregate as dfg
import pandas as pd
import numpy as np

reload(st_u)
reload(m_u)
reload(dfg)

logging.basicConfig(level=logging.INFO)


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
    df.loc[:, 'ramp_index'] = -1
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

    return df


class ProcessedBPMData:
    '''ResponseMatrix data measured and processed

    Contains now information of
    '''
    def __init__(self, df, columns_to_process=None):

        self._orig_df = df
        self._df = None
        self._agg = None
        self._measurement = None
        self._measurement_fit_data = None
        self._df_wr = None
        self._columns_to_process = columns_to_process
        # self._meas_ref = self_meas_ref.infer_objects()

    @property
    def original_dataframe(self):
        '''Original dataframe
        '''
        return self._orig_df

    @property
    def dataframe(self):
        '''Original dataframe with additional information but only selected columns

        Added:

            * measurement count
             * steerer_type
        '''
        if self._df is None:
            self._to_dataframe()
        return self._df

    @property
    def agg(self):
        '''Aggregated by measurement step

        First measurement skipped for vector data: First bpm reading is not
        reliable.
        '''
        if self._agg is None:
            self._to_agg()
        return self._agg

    @property
    def measurement_data(self):
        '''Data flagged as measurement data
        '''
        if self._measurement is None:
            self._to_measurement()
        return self._measurement

    @property
    def measurement_fit_data(self):
        '''Data flagged as measurement data
        '''
        if self._measurement_fit_data is None:
            self._to_measurement_fit_data()
        return self._measurement_fit_data

    @property
    def processed_dataframe(self):
        if self._df_wr is None:
            self._to_processed_dataframe()
        return self._df_wr

    # ----------------------------------------------------------------------
    # Lazy procecssing
    def _to_dataframe(self):
        # Check with ipython notebook if intermediate steps are appropriate
        df = prepare_dataframe(self.original_dataframe,
                               columns_to_process=self._columns_to_process)

        df = add_measurement_counts(df, copy=False)
        df = add_steerer_info(df, copy=False)
        df = df.infer_objects()

        self._df = df

    def _to_agg(self):
        df = self.dataframe
        agg = dfg.df_with_vectors_mean_skip_first(df)
        assert(df.shape[0]/agg.shape[0] == 3)
        self._agg = agg

    def _to_measurement(self):
        agg = self.agg
        table_meas = agg.loc[agg.bk_dev_mode == 'store_data']
        table_meas = table_meas.infer_objects()
        table_meas = m_u.add_measurement_index(table_meas)
        self._measurement = table_meas

    def _to_measurement_fit_data(self):
        table_meas = self.measurement_data
        self._measurement_fit_data = bpm_data.calc_bpm_gains(table_meas)

    def _to_processed_dataframe(self):
        measurement = self.measurement_data
        measure_fit = self.measurement_fit_data
        measure_fit = measure_fit.set_index('sc_selected')
        df_wr = bpm_data.calc_bpm_ref(measurement, measure_fit)
        df_wr = bpm_data.add_bpm_scale(df_wr, copy=False)
        df_wr = bpm_data.add_bpm_deviation_from_fit(df_wr, copy=False)
        self._df_wr = df_wr
