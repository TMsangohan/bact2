'''Postprocess measured data for transverse beam dynamics analysis
'''
import logging
from ..utils import utils as m_u
from . import bpm_data
from ...pandas.dataframe import df_aggregate as dfg
import pandas as pd
import numpy as np


logger = logging.getLogger('bact')


def round_float_values(values, rounding_scale=1e6):
    values = np.asarray(values)
    nvals = values * rounding_scale
    nvals = nvals.astype(np.int_)
    nvals = nvals / rounding_scale
    return nvals


cols_to_process_default = [
    'time',
    'bpm_x_ref', 'bpm_y_ref',
    'bpm_x_diff', 'bpm_y_diff',
    'bpm_x_ref2', 'bpm_y_ref2',
    'bpm_x_diff2', 'bpm_y_diff2',
    'measurement',
    'I_rounded',
    'ramp_index',
    'bpm_waveform_x_pos', 'bpm_waveform_y_pos',
    'bpm_waveform_ds',
    'dt',
    'bpm_x_scale', 'bpm_y_scale',
]


def prepare_dataframe(df, columns_to_process=None,
                      column_to_round=None):

    assert(columns_to_process is not None)
    if columns_to_process is None:
        columns_to_process = cols_to_process_default

    assert(column_to_round is not None)

    df = df.reindex(columns=columns_to_process, index=df.index)

    try:
        round_col = df.loc[:, column_to_round]
    except Exception:
        logger.error('Known colums are {}'.format(df.columns))
        raise
    df.loc[:, 'I_rounded'] = round_float_values(round_col)
    df.loc[:, 'measurement'] = -1
    df.loc[:, 'steerer_pos'] = -1
    df.loc[:, 'ramp_index'] = -1
    return df


def add_measurement_counts(df, copy=True, columns=None):
    '''

    Todo:
       check if the addional copy is required
    '''
    if copy:
        df = df.copy()

    count = m_u.add_measurement_counts_progressive
    tt = count(df, copy=copy, columns=columns, count_column='measurement')
    tt.loc[:, 'measurement'] = pd.to_numeric(tt.measurement)
    return tt


class ProcessedBPMDataCommon:
    '''ResponseMatrix data measured and processed

    Contains now information of
    '''
    column_to_round = None
    columns_for_measurement_count = None
    column_for_selected_device = None
    column_for_selected_device_indep = None
    column_for_selected_device_indep_ref = None

    def __init__(self, df, columns_to_process=None):

        self._orig_df = df
        self._df = None
        self._agg = None
        self._measurement = None
        self._measurement_fit_data = None
        self._df_wr = None

        if columns_to_process is None:
            columns_to_process = cols_to_process_default

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
    def _to_dataframe_step1(self):
        # Check with ipython notebook if intermediate steps are appropriate
        df = prepare_dataframe(self.original_dataframe,
                               columns_to_process=self._columns_to_process,
                               column_to_round=self.column_to_round
                               )

        cols = self.columns_for_measurement_count
        assert(cols is not None)

        df = add_measurement_counts(df, copy=False, columns=cols)
        return df

    def _to_dataframe(self):
        df = self._to_dataframe_step1()
        df = df.infer_objects()
        self._df = df

    def _to_agg(self):
        df = self.dataframe
        agg = dfg.df_with_vectors_mean_skip_first(df)

        n_expected = 3
        df_shape = df.shape
        agg_shape = agg.shape
        n_sample = df_shape[0]/agg_shape[0]
        if n_sample != n_expected:
            txt = (
                f'Expected {n_expected} readings'
                f' but got {n_sample} readings per measurement:'
                f' orginal shape {df_shape} shape now {agg_shape}'
            )
            logger.error(txt)
            # raise AssertionError(txt)

        self._agg = agg

    def _to_measurement(self):
        '''
        Todo:
           check if it should be moved to response matrix
        '''
        agg = self.agg
        table_meas = agg.loc[agg.bk_dev_mode == 'store_data']
        table_meas = table_meas.infer_objects()
        t_col = self.column_for_selected_device
        table_meas = m_u.add_measurement_index(table_meas, column=t_col)
        self._measurement = table_meas

    def _to_measurement_fit_data(self):
        table_meas = self.measurement_data

        sel_dev = self.column_for_selected_device
        assert(sel_dev is not None)
        sel_dev_indep = self.column_for_selected_device_indep
        assert(sel_dev_indep is not None)
        sel_dev_indep_ref = self.column_for_selected_device_indep_ref
        if sel_dev_indep_ref is None:
            logger.debug('No column for reference value given')

        r = bpm_data.calc_bpm_gains(table_meas, column_name=sel_dev,
                                    indep_column=sel_dev_indep,
                                    indep_ref_column=sel_dev_indep_ref)
        self._measurement_fit_data = r

    def _to_processed_dataframe(self):
        measurement = self.measurement_data
        measure_fit = self.measurement_fit_data

        sel_dev = self.column_for_selected_device
        assert(sel_dev is not None)
        sel_dev_indep = self.column_for_selected_device_indep
        sel_dev_indep_ref = self.column_for_selected_device_indep_ref

        measure_fit = measure_fit.set_index(sel_dev)
        df_wr = bpm_data.calc_bpm_ref(measurement, measure_fit,
                                      column_name=sel_dev,
                                      indep_column=sel_dev_indep,
                                      indep_ref_column=sel_dev_indep_ref)
        # df_wr = bpm_data.add_bpm_scale(df_wr, copy=False, column_name=sel_dev)
        df_wr = bpm_data.add_bpm_deviation_from_fit(df_wr, copy=False)
        self._df_wr = df_wr
