from bact2.applib.transverse_lib import reference_orbit, model_fits, model_fit_funcs
from bact2.applib.response_matrix import commons
import matplotlib.pyplot as plt
import numpy as np

import gzip
import pickle
import logging
import os.path
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bact2')


def prepare_bpm_data(df_sel, ref_row=0):

    ref = df_sel.iloc[ref_row, :]
    x0 = ref.bpm_waveform_x_pos
    y0 = ref.bpm_waveform_y_pos

    x = df_sel.bpm_waveform_x_pos
    y = df_sel.bpm_waveform_y_pos

    ds = df_sel.bpm_waveform_ds

    dx = x - x0
    dy = y - y0

    dx = np.array(dx.tolist(), np.float_)
    dy = np.array(dy.tolist(), np.float_)
    ds = np.array(ds.tolist(), np.float_)

    ds_m, dx_m, dy_m = model_fits.select_bpm_data_in_model(ds, dx, dy)

    bpm_data = reference_orbit.OrbitData(x=dx, y=dy, s=ds)
    bpm_data_m = reference_orbit.OrbitData(x=dx_m, y=dy_m, s=ds_m)

    return bpm_data, bpm_data_m


def plot_fit_data_one_coordinate(ref_data=None, bpm_data=None, bpm_data_m=None,
                                 ds=None, ds_bpm=None, axes=None, lines_scale=None):
    '''
    Args:
       lines_scale: scale each individal line. Typically used to get all plots
                    close to one line. Thus its much easier to see if the
                    excitation exhibits not linear content
    '''

    ax1, ax2, ax3 = axes

    # a polarity scale
    p_scale = 1

    this_line_scale = 1

    for row in range(ref_data.shape[0]):

        marker = 'x'
        linestyle = '-'

        if lines_scale is None:
            this_line_scale = p_scale
        else:
            this_line_scale = lines_scale[row]
            if this_line_scale is None:
                # If no scale was given use a default scale and
                # mark the line
                this_line_scale = 1./8.
                marker = '.'
                linestyle = ':'

        # BPM measurement data
        # A line helping the eye
        dx_row = bpm_data[row, :]
        dx_m_row = bpm_data_m[row, :]
        dx_ref_row = ref_data[row, :]

        pdx_row = dx_row * this_line_scale
        pdx_m_row = dx_m_row * this_line_scale
        pdx_ref_row = dx_ref_row * this_line_scale

        # The measured data
        line, = ax1.plot(ds_bpm, pdx_row, marker=marker)
        lcol = line.get_color()
        ax1.plot(ds_bpm, pdx_row, linestyle=linestyle, color=lcol,
                 linewidth=.25)

        # The fitted ones
        ax1.plot(ds,   pdx_ref_row, '+-', color=lcol, linewidth=.25)

        # Plotting the offset from the fit to all other data
        offset = dx_m_row - dx_ref_row
        poffset = offset * this_line_scale
        # offset = pdx_ref_row

        ax2.plot(ds, poffset, '+-', color=lcol, linewidth=.25)

        # relative difference only if significant measurement data
        # currently for bpm measurements above 0.05 mm
        bpm_min_measurement = 0.05
        idx = np.absolute(pdx_m_row) > bpm_min_measurement

        offset_sel = offset[idx]
        ds_sel = ds[idx]
        dx_ref_row_sel = dx_ref_row[idx]
        scale = offset_sel / dx_ref_row_sel
        pscale = scale #* this_line_scale
        ax3.plot(ds_sel, pscale, '.--', color=lcol, linewidth=.25)


def plot_fit_data(ref_data=None, bpm_data=None, bpm_data_m=None,
                  savename=None, lines_scale=None):

    fig = plt.figure(figsize=[16, 20])
    ax1_x = plt.subplot(321)
    ax2_x = plt.subplot(323)
    ax3_x = plt.subplot(325)
    ax1_y = plt.subplot(322)
    ax2_y = plt.subplot(324)
    ax3_y = plt.subplot(326)

    axes_x = [ax1_x, ax2_x, ax3_x]
    axes_y = [ax1_y, ax2_y, ax3_y]
    for coor in ('x', 'y'):

        if coor == 'x':
            axes = axes_x
        elif coor == 'y':
            axes = axes_y

        for ax in axes:
            ax.clear()

        rd = getattr(ref_data, coor)
        bd = getattr(bpm_data, coor)
        bdm = getattr(bpm_data_m, coor)

        plot_fit_data_one_coordinate(ref_data=rd, bpm_data=bd,
                                     bpm_data_m=bdm, ds=ref_data.s,
                                     ds_bpm=bpm_data.s[0],
                                     axes=axes,
                                     lines_scale=lines_scale)

        ax1, ax2, ax3 = axes
        ax1.set_xlabel('ds [m]')
        ax2.set_xlabel('ds [m]')
        ax3.set_xlabel('ds [m]')

        if coor == 'x':
            ax1.set_ylabel('x [mm]')
            ax2.set_ylabel('$\Delta$ x [mm]')
            ax3.set_ylabel('rx')
        elif coor == 'y':
            ax1.set_ylabel('y [mm]')
            ax2.set_ylabel('$\Delta$ y [mm]')
            ax3.set_ylabel('ry')

    fig.set_tight_layout(True)
    fig.savefig(savename)


def process_steerer(df, steerer_ps_name, coordinate=None, savename=None,
                    last_2D=True):

    ps2magnet = model_fits.steerer_power_converter_to_steerer_magnet
    steerer_name = ps2magnet(steerer_ps_name)

    df_sel = df.loc[(df.sc_selected == steerer_ps_name), :]
    bpm_data, bpm_data_m = prepare_bpm_data(df_sel)

    dI = df_sel.bk_dev_dI
    dI_max = dI.abs().max()
    dI_s = dI/dI_max

    op = model_fits.OrbitOffsetProcessor()
    op.reference_angle = 5e-5

    calc = model_fits.calculate_model_fits
    r = calc(orbit_processor=op, bpm_data=bpm_data_m,
             magnet_name=steerer_name, coordinate=coordinate,
             steerer_amplitude=dI_s, last_2D=last_2D)
    scale, res2D = r

    scaled_amplitude = model_fit_funcs.compute_scaling(dI_s, *res2D.x)
    logger.debug(f'Using following amplitudes for plot {scaled_amplitude}')
    ref_data = op.create_reference_data(magnet_name=steerer_name,
                                        scales=scaled_amplitude)

    # The standard fit plots
    plot_fit_data(ref_data=ref_data, bpm_data=bpm_data, bpm_data_m=bpm_data_m,
                  savename=savename)

    dI_sa = np.absolute(dI_s)
    _eps = 1e-6

    # Which scale to use for data without a scale
    lines_scale = np.where(dI_sa < _eps, None, 1/dI_s)

    # The  fit plots  with all data scaled to approximately one
    name, ext = os.path.splitext(savename)
    scaled_name = name + '_scaled' + ext

    # The scaled fit plots
    plot_fit_data(ref_data=ref_data, bpm_data=bpm_data, bpm_data_m=bpm_data_m,
                  savename=scaled_name, lines_scale=lines_scale)


def main_func():
    pickle_file_name = sys.argv[1]
    target_file_path = sys.argv[2]

    target_file_name = os.path.basename(target_file_path)
    file_name, ext = os.path.splitext(target_file_name)

    # preprocess the name
    plot_prefix, cnt, steerer_name, suffix, coordinate = file_name.split('_')

    n_dims = suffix
    if n_dims == '1d':
        last_2D = False
    elif n_dims == '2d':
        last_2D = True
    else:
        txt = (
            f'Expected token "1_d" or "2_d" but I do not know'
            f' how to process {n_dims}: file_name {target_file_name}'
        )
        raise AssertionError(txt)

    logger.info(
        f'Processing steerer {steerer_name} main coordinate {coordinate}'
    )

    ps_name = steerer_name

    with gzip.open(pickle_file_name) as fp:
        obj = pickle.load(fp)

    df = obj.processed_dataframe
    process_steerer(df, ps_name, coordinate=coordinate,
                    savename=target_file_path, last_2D=last_2D)
