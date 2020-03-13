from ..transverse_lib import bpm_plots
import matplotlib.pyplot as plt
import numpy as np
import logging
import os.path

logger = logging.getLogger('bact2')


def max_current(steerer_type):
    max_current = 1
    if (steerer_type == 'horizontal').all():
        max_current = 0.07/6.
    elif (steerer_type == 'vertical').all():
        max_current = 0.07
    else:
        assert(False)
    return max_current


def process_steerer(df, target_file_name, plot_dir=None):

    plot_file_name = os.path.basename(target_file_name)

    fn, ext = os.path.splitext(plot_file_name)
    plot_prefix, cnt, steerer_name, suffix, coordinate = fn.split('_')
    cnt = int(cnt)

    assert(suffix == 'main')
    assert(plot_dir is not None)

    one_steerer = df

    steerer_name = df.sc_selected
    steerer_name = list(set(steerer_name))
    # cnt = counter(steerer_name)

    assert(len(steerer_name) == 1)
    steerer_name = steerer_name[0]

    steerer_type = one_steerer.steerer_type

    if (steerer_type == 'horizontal').all():
        assert(coordinate == 'x')
        plt_label = r'$\Delta x$ [$\mu$ m]'
        plot_name_x = target_file_name
        plot_name_y = target_file_name.replace('main', 'sup_')
        st_type = 'h'
    elif (steerer_type == 'vertical').all():
        assert(coordinate == 'y')
        plt_label = r'$\Delta y$ [$\mu$ m]'
        plot_name_x = target_file_name.replace('main', 'sup_')
        plot_name_y = target_file_name
        st_type = 'v'
    else:
        assert(0)

    plot_name_x = os.path.join(plot_dir, plot_name_x)
    plot_name_y = os.path.join(plot_dir, plot_name_y)

    logger.info(f'Storing to files: for x {plot_name_x} for y {plot_name_y}')

    txt = f'Steerer {steerer_name}'
    logger.info(txt)
    plt.title(f'Steerer {steerer_name}')

    I = one_steerer.sc_sel_dev_setpoint
    I = I.values

    sf = one_steerer.bk_dev_scale_factor.values.mean()
    max_I = max_current(one_steerer.steerer_type)
    offset = one_steerer.bk_dev_current_offset.values.mean()

    def I_to_dIs(I, sf=sf, max_current=max_I, offset=offset):
        '''recalculate I to dI
        '''
        dI = I - offset
        dIs = dI / (sf * max_current)
        return dIs

    # dI = one_steerer.bk_dev_dI
    # dIs = dI / (sf * max_current)

    def dataframe_column_to_array(col):
        r = np.array(col.tolist(), np.float_)
        return r

    df_2_a = dataframe_column_to_array

    bpm_x_pos = df_2_a(one_steerer.bpm_waveform_x_pos)
    bpm_y_pos = df_2_a(one_steerer.bpm_waveform_y_pos)

    bpm_x_ref = df_2_a(one_steerer.bpm_x_ref)
    bpm_y_ref = df_2_a(one_steerer.bpm_y_ref)

    bpm_x_diff = df_2_a(one_steerer.bpm_x_diff)
    bpm_y_diff = df_2_a(one_steerer.bpm_y_diff)

    bpm_x_ref2 = df_2_a(one_steerer.bpm_x_ref2)
    bpm_y_ref2 = df_2_a(one_steerer.bpm_y_ref2)

    bpm_x_diff2 = df_2_a(one_steerer.bpm_x_diff2)
    bpm_y_diff2 = df_2_a(one_steerer.bpm_y_diff2)

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
