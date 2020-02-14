'''Produce plot collections for kicked beam

Plots give the following info:
* beam position monitor measurement for each beam position monitor
  versus each steerer
* the linear interpolation line
* the quadratic interpolation line
* the difference between the measurement and the linear
  interpolation line
* the difference between the measurement and the quadratic
  interpolation line

Furthermore arrow are included that indicate the scan direction

The difference between the measuremment and the interpolation
indicate a hysteresis effect of the steerer.

Some steerers seem to be not very effective

Todo:
    * the code should not need to guess the relative scaling
      factor
'''
import logging
from matplotlib.patches import Arrow
import matplotlib.pyplot as plt
import numpy as np
import os.path
from dataclasses import dataclass

logger = logging.getLogger('bact2')
logger.setLevel(logging.DEBUG)


def max_current(steerer_type):
    max_current = 1
    if (steerer_type == 'horizontal').all():
        max_current = 0.07/6.
    elif (steerer_type == 'vertical').all():
        max_current = 0.07
    else:
        assert(False)
    return max_current


def diff_s(vec):
    return vec[1] - vec[0]


@dataclass
class BpmData:
    pos: np.ndarray

    # Linear interpolation
    ref: np.ndarray
    diff: np.ndarray

    # Quadratic interpolation
    ref2: np.ndarray
    diff2: np.ndarray


def make_plot(I, I_to_dIs, bpm_data, axes_dict=None,
              cnt=None):

    assert(axes_dict is not None)
    cnt = int(cnt)

    # BPM Position versus current
    ax_label = f'bpm_diff_pos_{cnt}'
    # Second axis on the right
    axr_label = f'bpm_ref_pos_{cnt}'
    # Third axis on top
    axt_label = f'I_pos_{cnt}'

    try:
        ax = axes_dict[ax_label]
        has_subplots = True
    except KeyError:
        has_subplots = False

    if has_subplots:
        axr = axes_dict[axr_label]
        axt = axes_dict[axt_label]

    else:
        ax = plt.subplot(11, 10, cnt+1, label=ax_label)
        ax.set_label(ax_label)
        axes_dict[ax_label] = ax

        axr = ax.twinx()
        axr.set_label(axr_label)
        axes_dict[axr_label] = axr

        axt = ax.twiny()
        axt.set_label(axt_label)
        axes_dict[axt_label] = axt

    ax.clear()
    axr.clear()
    axt.clear()

    def calc_arrow_width(indep, dep):
        xl = indep.max() - indep.min()
        yl = dep.max() - dep.min()
        diag = np.sqrt(xl**2 + yl**2)
        return diag

    mm_to_um = 1000
    dep = bpm_data.diff * mm_to_um
    arrow_width = calc_arrow_width(I, dep)*1e-3
    arrow = Arrow(I[0], dep[0], diff_s(I), diff_s(dep),
                  width=arrow_width, color='r')
    ax.plot(I, dep, 'r.-')
    ax.add_patch(arrow)

    # Difference to quadratic interpolation
    ax.plot(I, bpm_data.diff2 * mm_to_um, 'm.-')
    # And the difference between quadratic prediction where it differs from the
    # linear part
    # Todo:
    #   scale should be a parameter
    diff_to_linear = (bpm_data.ref2 - bpm_data.ref) * mm_to_um
    ax.plot(I, diff_to_linear, 'm--')

    dep = bpm_data.pos

    arrow_width = calc_arrow_width(I, dep)*0.05
    arrow = Arrow(I[0], dep[0], diff_s(I), diff_s(dep),
                  width=arrow_width, color='b')
    axr.plot(I, dep, 'b.')
    axr.add_patch(arrow)

    # Quadratic interpolation
    axr.plot(I, bpm_data.ref,  'b-')
    axr.plot(I, bpm_data.ref2, 'c-')

    # update_dIs_scale()
    # x1, x2 = ax.get_xlim()
    axt.set_xlim(*I_to_dIs(ax.get_xlim()))

    [xt.set_color('r') for xt in ax.yaxis.get_ticklabels()]
    [xt.set_color('b') for xt in axr.yaxis.get_ticklabels()]


def make_plots(I, I_to_dIs, bpm_data, fig=None):
    '''make a plot for every different bpm reading

    These plots are expected to be executed for a single bpm reading.

    The plot will show:

    * the current range at the bottom scale
    * the relative current range on the top axis
    * the bpm reading to the right axis
    * the offset of the bpm reading to the fit to the left axis

    '''
    assert(fig is not None)
    # print('axes {}'.format(axes))

    # Create cache of available subplot axes
    sub_plots = {}
    axes = fig.get_axes()
    for ax in axes:
        sub_plots[ax.get_label()] = ax

    for i in range(bpm_data.pos.shape[1]):
        y = bpm_data.pos[:, i]
        # Linear part
        yr = bpm_data.ref[:, i]
        dy = bpm_data.diff[:, i]
        # Quadratic part
        yr2 = bpm_data.ref2[:, i]
        dy2 = bpm_data.diff2[:, i]
        bpm_slice = BpmData(pos=y, ref=yr, diff=dy, ref2=yr2, diff2=dy2)
        make_plot(I, I_to_dIs, bpm_slice, axes_dict=sub_plots, cnt=i)

    fig.set_tight_layout(tight=True)


def process_steerer(df, target_file_name, plot_dir=None):

    plot_file_name = os.path.basename(target_file_name)

    fn, ext = os.path.splitext(plot_file_name)
    plot_prefix, cnt, steerer_name, suffix, coordinate = fn.split('_')
    cnt = int(cnt)

    assert(suffix == 'main')

    if plot_dir is None:
        plot_dir = '/home/mfp/Devel/github/data/response_matrix/'

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
    bpm_data = BpmData(
        pos=bpm_x_pos,
        ref=bpm_x_ref, diff=bpm_x_diff,
        ref2=bpm_x_ref2, diff2=bpm_x_diff2
    )
    make_plots(I, I_to_dIs, bpm_data, fig=fig)
    fig.savefig(plot_name_x)

    logger.info(f'Now creating plots y storing to :  {plot_name_y}')
    bpm_data = BpmData(
        pos=bpm_y_pos,
        ref=bpm_y_ref, diff=bpm_y_diff,
        ref2=bpm_y_ref2, diff2=bpm_y_diff2,
    )
    make_plots(I, I_to_dIs, bpm_data, fig=fig)
    fig.savefig(plot_name_y)

    plt.close("all")
    del fig
