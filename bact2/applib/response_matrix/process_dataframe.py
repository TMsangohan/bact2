from ..utils import steerer as st_u, utils as m_u
from ..transverse_lib import process_dataframe

cols_to_process_default = process_dataframe.cols_to_process_default + [
    'sc_selected',
    'bk_dev_mode',
    'steerer_mode',
    'steerer_pos',
    'sc_sel_dev_setpoint', 'sc_sel_dev_readback',
    'steerer_type',
    'bk_dev_dI', 'bk_dev_scale_factor', 'bk_dev_current_offset',

]


def provide_steerer_sort(df):
    tmp = [st_u.SteererSort(*tup) for tup in zip(df.sc_selected, df.index)]
    tmp.sort()
    counter = m_u.Counter()
    for t in tmp:
        t.count = counter(t.name)
    return tmp


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


class ProcessedBPMData(process_dataframe.ProcessedBPMDataCommon):
    '''ResponseMatrix data measured and processed

    Contains now information of
    '''
    column_to_round = 'sc_sel_dev_setpoint'
    columns_for_measurement_count = ['sc_selected', 'bk_dev_mode', 'I_rounded']
    column_for_selected_device = 'sc_selected'
    column_for_selected_device_indep = 'sc_sel_dev_setpoint'
    column_for_selected_device_indep_ref = 'bk_dev_current_offset'

    # Lazy procecssing
    # def _to_dataframe_step1(self):
    #    # Check with ipython notebook if intermediate steps are appropriate
    #    df = prepare_dataframe(self.original_dataframe,
    #                           columns_to_process=self._columns_to_process,
    #                           column_to_round=self.column_to_round
    #                           )
    #
    #    df = add_measurement_counts(df, copy=False)
    #    return df

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('columns_to_process', cols_to_process_default)
        super().__init__(*args, **kwargs)

    def _to_dataframe(self):
        super()._to_dataframe()
        df = self._df
        assert(self._df is not None)
        df = add_steerer_info(df, copy=False)
        df = df.infer_objects()
        self._df = df
