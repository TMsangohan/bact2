from ..transverse_lib.model_fit_funcs import compute_reference_data
import numpy as np


def min_func_adjust_2D(params, *args, bpm_data=None, **kws):
    '''Minimize the radial offset
    '''

    n_pars = len(params)
    assert(n_pars % 2 == 0)
    l2 = n_pars // 2

    params_x = params[:l2]
    params_y = params[l2:]

    evaluate_coupling = kws.pop('evaluate_coupling', False)

    kws_x = kws['x']
    kws_y = kws['y']

    ref_x = compute_reference_data(params_x, *args, **kws_x)
    ref_y = compute_reference_data(params_y, *args, **kws_y)

    # Main part
    dval_x = bpm_data.x - ref_x.x
    dval_y = bpm_data.y - ref_y.y

    # Should not add too much ...
    if evaluate_coupling:
        dval_x += bpm_data.x - ref_x.x
        dval_y += bpm_data.y - ref_y.y

    dval2 = dval_x**2 + dval_y**2
    dval = np.sqrt(dval2)
    dval = np.ravel(dval)
    return dval
