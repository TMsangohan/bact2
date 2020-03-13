'''
'''
from bact2.applib.transverse_lib import (process_model_fits,
                                         model_fits, model_fit_funcs)
import logging
import numpy as np
import os.path

logger = logging.getLogger('bact2')


def process_steerer(df, steerer_ps_name, coordinate=None, savename=None,
                    last_2D=True):

    ps2magnet = model_fits.steerer_power_converter_to_steerer_magnet
    steerer_name = ps2magnet(steerer_ps_name)

    df_sel = df.loc[(df.sc_selected == steerer_ps_name), :]
    bpm_data, bpm_data_m = process_model_fits.prepare_bpm_data(df_sel)

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
    plot_fit_data = process_model_fits.plot_fit_data
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


def main():
    process_model_fits.main_func(process_func=process_steerer)


if __name__ == '__main__':
    main()
