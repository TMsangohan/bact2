from bact2.applib.response_matrix import reference_orbit
from . import model_fit_funcs

import scipy.optimize
import numpy as np
import functools
import logging

logger = logging.getLogger('bact2')

#: scaling factor of bpm data: these are in mm
bpm_scale_factor = 1./1000.


def steerer_power_converter_to_steerer_magnet(name):
    '''

    Todo:
        add thorough checks!
    '''
    index = 3
    assert(name[index] == 'p')
    magnet_name = name[:index] + 'm' + name[index+1:]
    return magnet_name.upper()


def select_bpm_data_in_model(ds, dx, dy):
    '''

    remove the missing bpm at position 165

    Keep first axis
    '''
    ds_ref = ds[0]
    bpms_in_model = np.absolute(ds_ref - 165) > 1e-5

    ds_m = ds[:, bpms_in_model]
    dx_m = dx[:, bpms_in_model]
    dy_m = dy[:, bpms_in_model]

    return ds_m, dx_m, dy_m


class OrbitOffsetProcessor:
    def __init__(self):
        orbit = reference_orbit.OrbitCalculator()

        orbit_data_ref = orbit.orbitData()
        orbit_offset_filter = reference_orbit.OrbitOffset()
        orbit_offset_filter.reference_data = orbit_data_ref

        self.orbit = orbit
        self.orbit_offset_filter = orbit_offset_filter
        self.orbit_data_ref = orbit_data_ref

        # 1 urad reference angle
        self.reference_angle = 1e-6


    @functools.lru_cache(maxsize=None)
    def compute_reference_model(self, magnet_name=None, scale=None):

        assert(magnet_name is not None)

        scaled_angle = self.reference_angle * scale
        logger.info(
            f'Computing model for scale {scaled_angle*1000:.3f} mrad'
            f' and magnet {magnet_name}'
        )

        od = self.orbit.orbitCalculatorForChangedMagnet(name=magnet_name,
                                                        angle=scaled_angle)
        off_orbit = od.orbitData()
        offset = self.orbit_offset_filter(off_orbit)

        return offset

    def _compute(self, magnet_name, scale):
        r = self.compute_reference_model(scale=scale, magnet_name=magnet_name)
        dx = r.bpm.x
        dy = r.bpm.y

        model_to_bpm = 1/bpm_scale_factor
        dxs = dx * model_to_bpm
        dys = dy * model_to_bpm
        r = reference_orbit.OrbitData(x=dxs, y=dys, s=r.bpm.s)
        return r

    def _combine_data(self, data):
        data = reference_orbit.OrbitData(
            x=np.array([md.x for md in data]),
            y=np.array([md.y for md in data]),
            s=self.orbit_data_ref.bpm.s
        )
        return data

    def create_model_data(self, magnet_name=None, scales=None):
        '''

        model data are all rescaled to scale 1
        '''
        def scaled_to_1(scale):
            data = self._compute(magnet_name, scale)
            xs = data.x/scale
            ys = data.y/scale
            r = reference_orbit.OrbitData(x=xs, y=ys, s=data.s)
            return r

        data = [scaled_to_1(scale) for scale in scales]
        return self._combine_data(data)

    def create_reference_data(self, magnet_name=None, scales=None):
        '''
        '''
        data = [
            self._compute(magnet_name, scale) for scale in scales
        ]
        return self._combine_data(data)


def calculate_model_fits(orbit_processor=None, bpm_data=None,
                         magnet_name=None,
                         steerer_amplitude=None,
                         coordinate=None, last_2D=True):
    '''Fit ocelot model to bpm data.

    This is done stepwise. It could be that a straight forwared fit
    could do the job too. In this manner it start, it starts with
    a simple scalar fit and then gets more complex for every step
    thereafter.

    Following steps are made...

    1. step linear scaling
    2. step cubic scaling using an appropriate model for each scale factor

    Args:
       last_2D: Shall the last iteration be a 2D fit of a fit to the main
                steerer coordinate (thus

    '''

    assert(orbit_processor is not None)
    assert(bpm_data is not None)

    steerer_amplitude = np.atleast_1d(steerer_amplitude)
    if len(steerer_amplitude.shape) != 1:
        raise AssertionError('steerer amplitude can only be a vector')

    # First step linear scaling
    t_max = steerer_amplitude.max()
    model_data = orbit_processor.create_model_data(magnet_name, [t_max])

    d = {
        'model_data': model_data, 'dI': steerer_amplitude, 'simple': True,
        'bpm_data': bpm_data,
        'coordinate': coordinate,
    }

    func = model_fit_funcs.min_single_coordinate
    jac = model_fit_funcs.jac_single_coordinate
    res_guess = scipy.optimize.least_squares(func, x0=(1,), jac=jac, kwargs=d)
    x0 = float(res_guess.x)

    logger.info(
        f'Magnet {magnet_name} Linear approximation scaling x={x0}'
        f' status={res_guess.status}'
    )

    scaled_amplitude = steerer_amplitude * x0
    # Now parabolic fit to the data
    d['simple'] = False
    d['dI'] = scaled_amplitude

    res_fit = scipy.optimize.least_squares(func, x0=(0, 1, 0), jac=jac,
                                           kwargs=d)

    logger.info(
        f'Magnet {magnet_name} Parabolic approximation scaling x={res_fit.x}'
        f' status={res_fit.status}'
    )

    # Now parabolic fit to the data but with model data for each
    # excitation
    compute_scaling = model_fit_funcs.compute_scaling
    t_par = np.array(res_fit.x) * x0
    logger.info(
        f'Magnet {magnet_name} recomputing reference data using pars {t_par}'
        f' scaling={x0}'
    )

    # I guess this time its good enough to go for the full fit to the
    # 2D data

    del d['coordinate']

    if last_2D:
        func = model_fit_funcs.min_func_adjust_2D
        jac = None
        info = 'x and y simultaneously'

    else:
        func = model_fit_funcs.min_single_coordinate
        jac = model_fit_funcs.jac_single_coordinate
        d['coordinate'] = coordinate
        info = f'coordinate {coordinate}'

    for i in range(2):
        scaled_amplitude = compute_scaling(steerer_amplitude, *t_par)
        model_data = orbit_processor.create_model_data(magnet_name=magnet_name,
                                                       scales=scaled_amplitude)

        d['model_data'] = model_data
        d['dI'] = steerer_amplitude
        logger.info(
            f'Using scaled amplitudes {scaled_amplitude}'
        )

        res2D = scipy.optimize.least_squares(func, x0=t_par, kwargs=d)
        t_par = res2D.x

        logger.info(
            f'Iteration {i} magnet {magnet_name} fit to {info}'
            f' with recomputed reference data gave {res2D.x}'
        )

    return x0, res2D
