'''functions for fitting single steerer measurement to data

Reference data calculation or offset calculation is
performed for both coordinates at the same time.

It is assumed that the superfluent computation can be
ignored. F

'''
from bact2.applib.response_matrix import reference_orbit
import numpy as np
import logging

logger = logging.getLogger('bact2')


def _to_parameters(params, simple=True):
    '''Linear or cubic model.


    '''
    if not simple:
        return params

    slope, = params
    slope = float(slope)
    intercept = 0
    parabola = 0

    return intercept, slope, parabola


def compute_scaling(indep, intercept, slope, parabola):
    '''
    Todo:
       check if np.polyval does the job
    '''
    scale = intercept + indep * (slope + indep * parabola)
    return scale


def compute_reference_data(params, simple=True, dI=None, model_data=None):

    assert(dI is not None)
    assert(model_data is not None)

    dI = np.atleast_1d(dI)
    t_pars = _to_parameters(params, simple=simple)
    scale = compute_scaling(dI, *t_pars)

    mdx = model_data.x
    mdy = model_data.y
    ref_x = mdx * scale[:, np.newaxis]
    ref_y = mdy * scale[:, np.newaxis]

    ref = reference_orbit.OrbitData(x=ref_x, y=ref_y, s=model_data.s)
    return ref


def min_single_coordinate(params, *args, bpm_data=None, coordinate=None, **kws):

    assert(bpm_data is not None)
    assert(coordinate is not None)

    ref_o = compute_reference_data(params, *args, **kws)
    ref = getattr(ref_o, coordinate)
    measurement = getattr(bpm_data, coordinate)
    dval = measurement - ref
    dval = np.ravel(dval)

    return dval


def jac_single_coordinate(params, *args, simple=True, dI=None, coordinate=None,
                          model_data=None, bpm_data=None):

    dI = np.atleast_1d(dI)
    intercept, slope, parabola = _to_parameters(params, simple=simple)
    # How many parameters
    if simple:
        m = 1
    else:
        m = 3

    # Some helper arrays with appropriate extra dimensions
    # These should be in the same order as for the function
    # Then the ravel below will not mess around
    md = getattr(model_data, coordinate)
    dIa = dI[:, np.newaxis]
    ones = np.ones(dIa.shape)

    # The contribution of the linear term ...
    # i.e. the slope factor
    linear = md * dIa

    linear_contrib = np.ravel(linear)

    if not simple:
        const = md * ones
        quadratic = md * (dIa)**2

        const_contrib = np.ravel(const)
        quadratic_contrib = np.ravel(quadratic)

    jac = np.zeros([linear_contrib.shape[0], m], np.float_)

    if simple:
        jac[:, 0] = linear_contrib
    else:
        jac[:, 0] = const_contrib
        jac[:, 1] = linear_contrib
        jac[:, 2] = quadratic_contrib

    # measurement data - model
    jac = -jac
    return jac


def min_func_adjust_2D(params, *args, bpm_data=None, **kws):
    '''Minimize the radial offset
    '''
    assert(bpm_data is not None)

    ref = compute_reference_data(params, *args, **kws)
    dval_x = bpm_data.x - ref.x
    dval_y = bpm_data.y - ref.y

    dval2 = dval_x**2 + dval_y**2
    dval = np.sqrt(dval2)
    dval = np.ravel(dval)
    return dval
