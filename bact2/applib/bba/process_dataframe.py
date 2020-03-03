from bact2.applib.transverse_lib import process_dataframe as pr_df
from ..utils import utils as m_u


def cols_to_process_default_func():

    new_cols = [
        'count_bpm_reads',
        'mux_selector_readback',
        'mux_selector_setpoint_num',
        'mux_selector_selected_num',
        'mux_selector_selected',
        'mux_power_converter_setpoint',
        'mux_power_converter_readback',
    ]

    cols = pr_df.cols_to_process_default + new_cols

    return cols


class ProcessedBPMData(pr_df.ProcessedBPMDataCommon):
    '''Adaptions for bba
    '''

    column_to_round = 'mux_power_converter_setpoint'
    columns_for_measurement_count = ['mux_selector_selected', 'I_rounded']
    column_for_selected_device = 'mux_selector_selected'
    # column_for_selected_device = 'mux_selector_setpoint_num'
    column_for_selected_device_indep = 'mux_power_converter_setpoint'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('columns_to_process', cols_to_process_default_func())
        super().__init__(*args, **kwargs)

    def _to_measurement(self):
        agg = self.agg
        table_meas = agg.infer_objects()
        col = self.column_for_selected_device
        table_meas = m_u.add_measurement_index(table_meas, column=col)
        self._measurement = table_meas
