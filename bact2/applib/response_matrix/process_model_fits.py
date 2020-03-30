'''
'''
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bact2')

from bact2.applib.transverse_lib import process_model_fits
from bact2.applib.transverse_lib import model_fits, model_fit_funcs
from bact2.applib.transverse_lib import magnet_info, reference_orbit

import numpy as np
import os.path


def process_steerer(df, steerer_ps_name, coordinate=None, savename=None,
                    last_2D=True):

    ps2magnet = magnet_info.steerer_power_converter_to_steerer_magnet
    steerer_name = ps2magnet(steerer_ps_name)

    tf = magnet_info.magnet_transfer_function(steerer_name)

    df_sel = df.loc[(df.sc_selected == steerer_ps_name), :]
    bpm_data, bpm_data_m = process_model_fits.prepare_bpm_data(df_sel)

    dI = df_sel.bk_dev_dI
    dI_max = dI.abs().max()
    dI_s = dI/dI_max

    angle_max = magnet_info.kicker_angle(steerer_name, current=dI_max,
                                         magnet_length=1)
    logger.info(f'Maximum angle found {angle_max} guessed')

    op = model_fits.OrbitOffsetProcessor(cell=reference_orbit.ncell)
    op.reference_angle = angle_max

    steerer_type = None
    if steerer_name[0] == 'H':
        steerer_type = 'x'
    elif steerer_name[0] == 'V':
        steerer_type = 'y'
    else:
        txt = f'Can not derive steerer type from name {steerer_name}'
        raise AssertionError(txt)

    if steerer_type == coordinate:
        pass
    else:
        steerer_name = steerer_name + '_artefact'
        logger.info(f'trying to evaluate artefact orbit for {steerer_name}')

    calc = model_fits.calculate_model_fits
    r = calc(orbit_processor=op, bpm_data=bpm_data_m,
             magnet_name=steerer_name, coordinate=coordinate,
             steerer_amplitude=dI_s, last_2D=last_2D,
             steps_to_execute=model_fits.StepsModelFit.fit_parabola)
    scale, res2D = r

    # Bpm's are in units of mm
    scale_model_data = 1000.0

    scaled_amplitude = model_fit_funcs.compute_scaling(dI_s, *res2D.x)
    logger.debug(f'Using following amplitudes for plot {scaled_amplitude}')
    ref_data = op.create_reference_data(magnet_name=steerer_name,
                                        scales=scaled_amplitude)

    # Same colour for same absolute excitation
    adI_s = np.absolute(dI_s)
    adI_s = np.round((adI_s * 100)).astype(np.int_)

    txt = (
        'Selecting colors based on rounded scaled relative'
        f' steerer excitation {adI_s}'
    )
    logger.debug(txt)
    line_colors_for_val = {0: 'k', 25: 'm', 50: 'r', 75: 'c', 100: 'b'}
    line_colors = [line_colors_for_val[val] for val in adI_s]

    t_title = f'Steerer {steerer_ps_name} scale factor {scale}'
    # The standard fit plots
    plot_fit_data = process_model_fits.plot_fit_data

    kws = {
        'ref_data': ref_data,
        'bpm_data': bpm_data,
        'bpm_data_m': bpm_data_m,
        'scale_model_data': scale_model_data,
        'line_colors': line_colors,
        'title': t_title,
        }
    plot_fit_data(savename=savename, **kws)

    dI_sa = np.absolute(dI_s)
    _eps = 1e-6

    # Which scale to use for data without a scale
    lines_scale = np.where(dI_sa < _eps, None, 1/dI_s)

    # The  fit plots  with all data scaled to approximately one
    name, ext = os.path.splitext(savename)
    scaled_name = name + '_scaled' + ext

    # The scaled fit plots
    plot_fit_data(savename=scaled_name, lines_scale=lines_scale, **kws)


def main():
    process_model_fits.main_func(process_func=process_steerer)


if __name__ == '__main__':
    main()
