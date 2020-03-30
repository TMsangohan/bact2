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
                                 offset=None, scale_model_data=None,
                                 ds=None, ds_bpm=None, axes=None,
                                 line_colors=None, lines_scale=None):
    '''
    Args:
       lines_scale: scale each individal line. Typically used to get all plots
                    close to one line. Thus its much easier to see if the
                    excitation exhibits not linear content
    '''

    if offset is None:
        offset = 0.0

    if scale_model_data is None:
        # Scale from model m to mm
        scale_model_data = 1000.0

    scale_model_data = float(scale_model_data)
    logger.info(f'Scaling model data by {scale_model_data}')

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

        # Model data are typically in meter while bpm data are in mm
        dx_ref_row = ref_data[row, :] * scale_model_data #- offset

        # For scaled plots
        pdx_row = dx_row * this_line_scale
        pdx_m_row = dx_m_row * this_line_scale
        pdx_ref_row = dx_ref_row * this_line_scale

        pdx_ref_row = pdx_ref_row

        # The measured data
        if line_colors is not None:
            t_color = line_colors[row]
        else:
            t_color = None

        # The measured bpm data
        line, = ax1.plot(ds_bpm, pdx_row, marker, color=t_color)
        lcol = line.get_color()


        # The measured bpm data line ... all measurements
        # ax1.plot(ds_bpm, pdx_row, linestyle=linestyle, color=lcol, linewidth=.1)
        #
        # The measured bpm data used for the fit: there is a bpm missing in the
        # model
        ax1.plot(ds_bpm, pdx_row, '.',
                 linestyle=linestyle,
                 color=lcol, linewidth=.1)

        # The fitted ones
        ax1.plot(ds,   pdx_ref_row, '-+', color=lcol, linewidth=.25)

        # Plotting the offset from the fit to all other data
        data_offset = dx_m_row - dx_ref_row
        poffset = data_offset * this_line_scale
        # offset = pdx_ref_row

        ax2.plot(ds, poffset, '+-', color=lcol, linewidth=.25)

        # relative difference only if significant measurement data
        # currently for bpm measurements above 0.05 mm
        bpm_min_measurement = 0.05
        idx = (
            np.absolute(pdx_ref_row) > bpm_min_measurement
        )

        data_offset_sel = data_offset[idx]
        ds_sel = ds[idx]
        dx_ref_row_sel = dx_ref_row[idx]
        scale = data_offset_sel / dx_ref_row_sel
        pscale = scale # * this_line_scale
        ax3.plot(ds_sel, pscale, '.--', color=lcol, linewidth=.25)


def plot_fit_data(ref_data=None, bpm_data=None, bpm_data_m=None, offset=None,
                  scale_model_data=None, lines_scale=None, line_colors=None,
                  title=None, savename=None):

    # Offsets only in x and y
    if offset is None:
        offset = (0.0, ) * 2

    offset_x, offset_y = offset

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
            t_offset = offset_x
        elif coor == 'y':
            axes = axes_y
            t_offset = offset_y

        for ax in axes:
            ax.clear()

        rd = getattr(ref_data, coor)
        bd = getattr(bpm_data, coor)
        bdm = getattr(bpm_data_m, coor)

        plot_fit_data_one_coordinate(ref_data=rd, bpm_data=bd, bpm_data_m=bdm,
                                     ds=ref_data.s, ds_bpm=bpm_data.s[0],
                                     scale_model_data=scale_model_data,
                                     offset=t_offset,
                                     axes=axes,
                                     line_colors=line_colors,
                                     lines_scale=lines_scale)

        ax1, ax2, ax3 = axes
        ax1.set_xlabel('ds [m]')
        ax2.set_xlabel('ds [m]')
        ax3.set_xlabel('ds [m]')

        if coor == 'x':
            ax1.set_ylabel('x [mm]')
            ax2.set_ylabel(r'$\Delta$ x [mm]')
            ax3.set_ylabel('rx')
        elif coor == 'y':
            ax1.set_ylabel('y [mm]')
            ax2.set_ylabel(r'$\Delta$ y [mm]')
            ax3.set_ylabel('ry')

    if title is not None:
        ax1.set_title(title)
    fig.set_tight_layout(True)
    fig.savefig(savename)


def main_func(process_func):
    pickle_file_name = sys.argv[1]
    target_file_path = sys.argv[2]

    dir_name = os.path.dirname(target_file_path)
    target_file_name = os.path.basename(target_file_path)
    file_name, ext = os.path.splitext(target_file_name)

    # preprocess the name
    plot_prefix, cnt, kicker_name, suffix, coordinate = file_name.split('_')

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
        f'Processing kicker {kicker_name} main coordinate {coordinate}'
    )

    with gzip.open(pickle_file_name) as fp:
        obj = pickle.load(fp)

    df = obj.processed_dataframe

    for t_coordinate in ['x', 'y']:
        if t_coordinate != coordinate:
            savename = target_file_name.replace(coordinate, t_coordinate)
        else:
            savename = target_file_name

        savepath = os.path.join(dir_name, savename)
        process_func(df, kicker_name, coordinate=t_coordinate,
                     savename=savepath, last_2D=last_2D)
