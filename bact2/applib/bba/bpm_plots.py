from ..transverse_lib import bpm_plots
import matplotlib.pyplot as plt
import numpy as np
import logging
import os.path

logger = logging.getLogger('bact2')


def process_quadrupoles(df, target_file_name, plot_dir=None):

    plot_file_name = os.path.basename(target_file_name)

    fn, ext = os.path.splitext(plot_file_name)
    plot_prefix, cnt, kicker_name, suffix, coordinate = fn.split('_')
    cnt = int(cnt)

    assert(suffix == 'main')
    assert(plot_dir is not None)

    one_kicker = df

    kicker_name = df.mux_selector_selected
    kicker_name = list(set(kicker_name))
    # cnt = counter(kicker_name)

    assert(len(kicker_name) == 1)
    kicker_name = kicker_name[0]

    plt_label = r'$\Delta x$ [$\mu$ m]'
    plot_name_x = target_file_name.replace('main_y', 'main_x')

    plt_label = r'$\Delta y$ [$\mu$ m]'
    plot_name_y = target_file_name

    plot_name_x = os.path.join(plot_dir, plot_name_x)
    plot_name_y = os.path.join(plot_dir, plot_name_y)

    logger.info(f'Storing to files: for x {plot_name_x} for y {plot_name_y}')

    txt = f'Kicker {kicker_name}'
    logger.info(txt)
    plt.title(f'Kicker {kicker_name}')

    I = one_kicker.mux_power_converter_setpoint
    I = I.values

    I_max = I.max()

    def I_to_dIs(vals):
        return vals/I_max

    def dataframe_column_to_array(col):
        r = np.array(col.tolist(), np.float_)
        return r

    df_2_a = dataframe_column_to_array

    bpm_x_pos = df_2_a(one_kicker.bpm_waveform_x_pos)
    bpm_y_pos = df_2_a(one_kicker.bpm_waveform_y_pos)

    bpm_x_ref = df_2_a(one_kicker.bpm_x_ref)
    bpm_y_ref = df_2_a(one_kicker.bpm_y_ref)

    bpm_x_diff = df_2_a(one_kicker.bpm_x_diff)
    bpm_y_diff = df_2_a(one_kicker.bpm_y_diff)

    bpm_x_ref2 = df_2_a(one_kicker.bpm_x_ref2)
    bpm_y_ref2 = df_2_a(one_kicker.bpm_y_ref2)

    bpm_x_diff2 = df_2_a(one_kicker.bpm_x_diff2)
    bpm_y_diff2 = df_2_a(one_kicker.bpm_y_diff2)

    fig = plt.figure(figsize=[30, 30])
    logger.info(f'Now creating plots x storing to :  {plot_name_x}')

    bpm_data = bpm_plots.BpmData(
        pos=bpm_x_pos,
        ref=bpm_x_ref, diff=bpm_x_diff,
        ref2=bpm_x_ref2, diff2=bpm_x_diff2
    )
    bpm_plots.make_plots(I, I_to_dIs, bpm_data, fig=fig)
    fig.savefig(plot_name_x)

    logger.info(f'Now creating plots y storing to :  {plot_name_y}')
    bpm_data = bpm_plots.BpmData(
        pos=bpm_y_pos,
        ref=bpm_y_ref, diff=bpm_y_diff,
        ref2=bpm_y_ref2, diff2=bpm_y_diff2,
    )
    bpm_plots.make_plots(I, I_to_dIs, bpm_data, fig=fig)
    fig.savefig(plot_name_y)

    plt.close("all")
    del fig
