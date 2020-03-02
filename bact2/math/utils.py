import numpy as np


def compare_value(value, reference_value, *, eps_abs=None, eps_rel=None):
    '''compare if values are equal within given limits

    Args:
        value:           value to check
        reference_value: reference value
        eps_abs:         absolute tolerance
        eps_rel:         relative tolerance

    Returns:
         0 if in range
         1 if value > reference_value
        -1 if value < reference_value

    Todo:
        Check if not available in a standard library function
    '''
    assert(eps_abs is not None)
    assert(eps_rel is not None)
    assert(eps_abs > 0)
    assert(eps_rel > 0)

    a_ref_val = np.absolute(reference_value)
    allowed_diff = eps_rel * a_ref_val + eps_abs
    diff = value - reference_value

    adiff = np.absolute(diff)
    if adiff <= allowed_diff:
        return 0
    elif diff > 0:
        return 1
    else:
        return -1

    raise AssertionError('Should not end up here')
