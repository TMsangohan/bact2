from ..transverse_lib.model_fit_funcs import min_single_coordinate, jac_single_coordinate
from ..transverse_lib.model_fits import OrbitOffsetProcessor, StepsModelFit
import scipy.optimize
import numpy as np
import logging
import functools

logger = logging.getLogger('bact2')


class OrbitOffsetProcessor(OrbitOffsetProcessor):

    # @functools.lru_cache(maxsize=None)
    def compute_quadrupole_reference_model(self, magnet_name=None, scale=None,
                                           dx=None, dy=None):

        logger.info(
            f'Computing model for relative scale change of k1 {scale} dx {dx} dy {dy}'
            f' and magnet {magnet_name}'
        )

        od = self.orbit.orbitCalculatorForChangedQuadrupole(name=magnet_name,
                                                            rk1=scale, dx=dx, dy=dy)
        off_orbit = od.orbitData()
        offset = self.orbit_offset_filter(off_orbit)

        ox = offset.bpm.x.max()
        oy = offset.bpm.y.max()
        logger.debug(f'offset max {ox} {oy}')
        return offset

    def compute_reference_model(self, magnet_name=None, scale=None,
                                dx=None, dy=None):
        assert(magnet_name is not None)
        assert(magnet_name[0] == 'Q')
        return self.compute_quadrupole_reference_model(magnet_name=magnet_name,
                                                       scale=scale, dx=dx, dy=dy)


    def create_model_data(self, *args, scale_model_data=False, **kws):
        '''

        Scaling does not make sense for quadrupole offset
        '''
        scale = scale_model_data
        scale = False
        return super().create_model_data(*args, scale_model_data=scale, **kws)

def calculate_model_fits(orbit_processor=None, bpm_data=None,
                         magnet_name=None, k1_amplitude_scaled=None,
                         coordinate=None, last_2D=True, steps_to_execute=None,
                         start_dx=None, start_dy=None):
    '''Fit ocelot model to bpm data.

    This is done stepwise. It could be that a straight forwared fit
    could do the job too. In this manner it start, it starts with
    a simple scalar fit and then gets more complex for every step
    thereafter.

    Following steps are made...

    1. step linear scaling

    '''

    assert(orbit_processor is not None)
    assert(bpm_data is not None)

    if steps_to_execute is None:
        steps_to_execute = StepsModelFit.estimate_scale
    else:
        steps_to_execute = StepsModelFit(steps_to_execute)

    k1_amplitude_scaled = np.atleast_1d(k1_amplitude_scaled)
    if len(k1_amplitude_scaled.shape) != 1:
        raise AssertionError('k1 amplitude can only be a vector')


    # if start_dx is None:
    #     start_dx = 0.1

    # if start_dy is None:
    #     start_dy = 0.1

    # First step linear scaling
    t_max = k1_amplitude_scaled.max()

    dx = dy = 0.0
    if coordinate == 'x':
        dx = start_dy
    elif coordinate == 'y':
        dy = start_dy
    else:
        raise AssertionError(f'Coordinate {coordinate} should be x or y')

    logger.info(f'For {magnet_name} computing model data using dx {dx} dy {dy} t_max = {t_max}')
    model_data = orbit_processor.create_model_data(magnet_name, scales=[t_max],
                                                   dx=dx, dy=dy)

    d = {
        'model_data': model_data, 'dI': k1_amplitude_scaled, 'simple': True,
        'bpm_data': bpm_data,
        'coordinate': coordinate,
    }

    func = min_single_coordinate
    jac = jac_single_coordinate
    res_guess = scipy.optimize.least_squares(func, x0=(1,), jac=jac, kwargs=d)
    x0 = float(res_guess.x)

    txt = (
        f'Magnet {magnet_name} Linear approximation scaling x={x0}'
        f' status={res_guess.status}'
    )
    logger.info(txt)

    if steps_to_execute <= StepsModelFit.estimate_scale:
        res_guess.x = (0, x0, 0)
        return x0, res_guess

    raise NotImplementedError('Following code not yet used for bba')

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
