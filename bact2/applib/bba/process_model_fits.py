import logging
logging.basicConfig(level=logging.INFO)

from bact2.applib.bba import model_fits
from bact2.applib.transverse_lib import process_model_fits, model_fit_funcs
import numpy as np
import os.path

logger = logging.getLogger('bact2')
logger.setLevel(level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)


def process_quadrupole(df, quadrupole_name, coordinate=None, savename=None,
                       last_2D=True):
    '''

    Todo:
        * Fix that the proper quadrupole current value is looked up
          Currently using hard coded dI_ref

        * Process kicks of the quadrupole i.e. displaced quadrupole
    '''
    df_sel = df.loc[df.mux_selector_selected == quadrupole_name, :]
    bpm_data, bpm_data_m = process_model_fits.prepare_bpm_data(df_sel)

    dI = df_sel.mux_power_converter_setpoint
    dI_ref = 265

    dI_s = dI / dI_ref

    op = model_fits.OrbitOffsetProcessor()

    # Modell data in m
    start_dx = .1 / 1000
    start_dy = .1 / 1000

    kws = {
        'orbit_processor': op,
        'bpm_data': bpm_data_m,
        'magnet_name':  quadrupole_name,
        'k1_amplitude_scaled': dI_s,
        'last_2D': last_2D,
        'start_dx': start_dx,
        'start_dy': start_dy
        }
    calc = model_fits.calculate_model_fits
    r = calc(coordinate='x', **kws)
    scale_x, res2D = r

    calc = model_fits.calculate_model_fits
    r = calc(coordinate='y', **kws)
    scale_y, res2D = r

    # scale_x = -5.6
    # scale_y = 8.13

    dx = start_dx * scale_x
    dy = start_dy * scale_y

    logger.info(f'Found an offset of dx {dx * 1000:.3} mm dy {dy*1000:.3} mm')
    #logger.debug(
    #    f'Reprocessing scaling amplitudes using original_data {dI_s}'
    #    f' and scales {res2D.x}'
    #)

    # if start_dx is None:
    #     start_dx = 0.1

    # if start_dy is None:
    #     start_dy = 0.1


    #dx = dy = 0
    #if coordinate == 'x':
    #    dx = start_dx
    #elif coordinate == 'y':
    #    dy = start_dy
    #else:
    #    raise AssertionError

    scaled_amplitude = model_fit_funcs.compute_scaling(dI_s, *(0, 1, 0))
    logger.debug(f'Using following amplitudes for plot {scaled_amplitude}')
    ref_data = op.create_reference_data(magnet_name=quadrupole_name,
                                        scales=dI_s,
                                        # scales=(0, 0, 0, 0),
                                        dx=dx,
                                        dy=dy)


    # The standard fit plots
    plot_fit_data = process_model_fits.plot_fit_data
    plot_fit_data(ref_data=ref_data, bpm_data=bpm_data, bpm_data_m=bpm_data_m,
                  offset=(dx, dy), lines_scale=None, savename=savename)

    return

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
    process_model_fits.main_func(process_quadrupole)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    #plt.ion()
    main()
    #plt.ioff()
    #plt.show()
