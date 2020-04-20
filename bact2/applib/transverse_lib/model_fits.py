from . import reference_orbit, model_fit_funcs, magnet_info

import scipy.optimize
import numpy as np
import functools
import logging
import enum

logger = logging.getLogger('bact2')

#: scaling factor of bpm data: these are in mm
bpm_scale_factor = 1./1000.


def select_bpm_data_in_model(ds, arrays):
    '''

    remove the missing bpm at position 165

    Keep first axis
    '''
    ds_ref = ds[0]
    bpms_in_model = np.absolute(ds_ref - 165) > 1e-5

    ds_m = ds[:, bpms_in_model]
    
    r = [a[:, bpms_in_model] for a in arrays]
    # dx_m = dx[:, bpms_in_model]
    # dy_m = dy[:, bpms_in_model]

    return ds_m, r


class OrbitOffsetProcessor:
    def __init__(self, **kws):
        orbit = reference_orbit.OrbitCalculator(**kws)

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

    def _compute(self, magnet_name=None, scale=None, scale_to_bpm_units=False,
                 **kws):
        r = self.compute_reference_model(scale=scale, magnet_name=magnet_name,
                                         **kws)
        dx = r.bpm.x
        dy = r.bpm.y

        ox = dx.max()
        oy = dy.max()

        logger.debug(f'_compute: offset max dx {ox} dy {oy}')

        if not scale_to_bpm_units:
            dxs, dys = dx, dy
        else:
            model_to_bpm = 1/bpm_scale_factor
            txt = (
                'Scaling model data to bpm units:'
                f' scaling factor = {model_to_bpm}!'
            )
            logger.warning(txt)
            dxs = dx * model_to_bpm
            dys = dy * model_to_bpm

            ox = dxs.max()
            oy = dys.max()
            logger.debug(f'_compute: offset scaled max dxs {ox} dys {oy}')

        r = reference_orbit.OrbitData(x=dxs, y=dys, s=r.bpm.s)
        return r

    def _combine_data(self, data):
        data = reference_orbit.OrbitData(
            x=np.array([md.x for md in data]),
            y=np.array([md.y for md in data]),
            s=self.orbit_data_ref.bpm.s
        )
        return data

    def create_model_data(self, magnet_name=None, scales=None,
                          scale_model_data=True, **kws):
        '''

        model data are all rescaled to scale 1
        '''
        def scaled_to_1(scale):
            data = self._compute(magnet_name=magnet_name, scale=scale, **kws)
            xs = data.x
            ys = data.y
            if scale_model_data:
                xs = xs/scale
                ys = ys/scale

            ox = xs.max()
            oy = ys.max()
            logger.debug(f'scaled to 1: offset scaled max {ox} {oy}')

            r = reference_orbit.OrbitData(x=xs, y=ys, s=data.s)
            return r

        data = [scaled_to_1(scale) for scale in scales]
        return self._combine_data(data)

    def create_reference_data(self, magnet_name=None, scales=None, **kws):
        '''
        '''
        data = [
            self._compute(magnet_name, scale, **kws) for scale in scales
        ]
        return self._combine_data(data)


class StepsModelFit(enum.IntEnum):
    '''How
    '''
    estimate_scale = 1
    fit_parabola = 2
    all_steps = 10


def calculate_model_fits(orbit_processor=None, bpm_data=None,
                         magnet_name=None, steerer_amplitude=None,
                         coordinate=None, last_2D=True, steps_to_execute=None):
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

    if steps_to_execute is None:
        steps_to_execute = StepsModelFit.all_steps
    else:
        steps_to_execute = StepsModelFit(steps_to_execute)

    steerer_amplitude = np.atleast_1d(steerer_amplitude)
    if len(steerer_amplitude.shape) != 1:
        raise AssertionError('steerer amplitude can only be a vector')

    # First step linear scaling
    t_max = steerer_amplitude.max()
    model_data = orbit_processor.create_model_data(magnet_name, [t_max],
                                                   scale_to_bpm_units=False)

    ref_data = model_fit_funcs.compute_reference_data([1], simple=True,
                                                      dI=steerer_amplitude,
                                                      model_data=model_data)

    t_bpm_data = getattr(bpm_data, coordinate)
    t_ref_data = getattr(ref_data, coordinate)

    t_ref = t_ref_data.ravel()[:, np.newaxis]
    t_bpm = t_bpm_data.ravel()
    t_bpm = t_bpm * bpm_scale_factor

    res_guess = scipy.optimize.lsq_linear(t_ref, t_bpm)
    assert(res_guess.success)
    x0 = res_guess.x

    txt = (
        f'Magnet {magnet_name} Linear approximation scaling x={x0}'
        f' status={res_guess.status}'
    )
    logger.info(txt)

    if steps_to_execute <= StepsModelFit.estimate_scale:
        res_guess.x = (0, x0, 0)
        return x0, res_guess

    d = {
        'model_data': model_data, 'dI': steerer_amplitude, 'simple': False,
        'bpm_data': bpm_data, 'coordinate': coordinate,
    }
    jac = model_fit_funcs.jac_single_coordinate
    t_ref = - jac([1, 1, 1], **d)

    res_fit = scipy.optimize.lsq_linear(t_ref, t_bpm)
    assert(res_fit.success)

    logger.info(
        f'Magnet {magnet_name} Parabolic approximation scaling x={res_fit.x}'
        f' status={res_fit.status}'
    )

    # As I use linear fits now I do not see the point in using scaled fits
    # Fur
    # Create fit matrix ...
    # scaled_amplitude = steerer_amplitude * x0

    # # Now scale the parameters by the scale factor
    # t_par = np.array(res_fit.x) * x0

    # I guess this time its good enough to go for the full fit to the
    # 2D data
    if steps_to_execute <= StepsModelFit.fit_parabola:
        return res_fit.x, res_fit

    # Now parabolic fit to the data but with model data for each
    # excitation
    compute_scaling = model_fit_funcs.compute_scaling
    logger.info(
        f'Magnet {magnet_name} recomputing reference data using pars {t_par}'
        f' scaling={x0}'
    )

    del d['coordinate']

    func = model_fit_funcs.min_single_coordinate
    jac_sc = model_fit_funcs.jac_single_coordinate

    if last_2D:
        func = model_fit_funcs.min_func_adjust_2D
        jac = None
        info = 'x and y simultaneously'
    else:
        func = model_fit_funcs.min_single_coordinate
        jac = jac_sc
        d['coordinate'] = coordinate
        info = f'coordinate {coordinate}'

    for i in range(2):
        scaled_amplitude = compute_scaling(steerer_amplitude, *t_par)
        model_data = orbit_processor.create_model_data(magnet_name=magnet_name,
                                                       scales=scaled_amplitude,
                                                       scale_to_bpm_units=False,
                                                       scale_model_data=False)
        d['dI'] = scaled_amplitude
        if last_2D:
            t_ref_x = - jac_sc([1, 1, 1], coordinate='x', **d)
            t_ref_y = - jac_sc([1, 1, 1], coordinate='y', **d)
            t_ref = np.concatenate([t_ref_x, t_ref_y], axis=0)
            t_bpm_all = np.concatenate([bpm_data.x.ravel(), bpm_data.y.ravel()],
                                       axis=0)
        else:
            t_ref = - jac_sc([1, 1, 1], **d)
            t_bpm_all = getattr(bpm_data, coordinate).ravel()

        t_bpm_all = t_bpm_all * bpm_scale_factor
        res2D = scipy.optimize.lsq_linear(t_ref, t_bpm_all)
        assert(res_fit.success)
        t_par = res2D.x
        continue

        d['model_data'] = model_data
        d['dI'] = steerer_amplitude
        logger.info(
            f'Using scaled amplitudes {scaled_amplitude}'
        )

        model_data = orbit_processor.create_model_data(magnet_name=magnet_name,
                                                       scales=scaled_amplitude,
                                                       scale_to_bpm_units=False)
        res2D = scipy.optimize.least_squares(func, x0=t_par, kwargs=d)
        t_par = res2D.x

        logger.info(
            f'Iteration {i} magnet {magnet_name} fit to {info}'
            f' with recomputed reference data gave {res2D.x}'
        )

    return x0, res2D
