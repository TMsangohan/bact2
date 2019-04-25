"""

Todo:
    Review proper place for exceptions
    See if vector checks are already provided by a standard package
"""
import numpy as np
import logging
logger = logging.getLogger("bact2")

class Bact2AssertionError(AssertionError):
    """

    Todo:
        Find a proper place for the exception
    """
    pass


class Bact2ValueError(ValueError):
    """

    Todo:
        Find a proper place for the exception
    """

def check_is_vector(vec):
    """

    Input:
        vec : a numpy array with one dimension

    Raises:
         An AssertionError if vec is not an array
    Todo:
        replace with a generic function if existant ...
    """
    shape = vec.shape
    l = len(shape)
    if l != 1:
        msg = "received vector with shape {} has not exactly one dimension: vector {}"
        logger.error(msg.format(shape, vec))
        msg = "received vector with shape {} has not exactly one dimension"
        raise Bact2AssertionError(msg.format(shape))


def unpack_vector_to_matrix(vec, n_vecs = None):
    """unpack a vector of data to its different vectors which are
    all of the same length

    Args:
        vec : the data vector (or packed data)
        n_vecs : number of equal length vectors the vector actually
                 contains

    Returns:
        a two dimensional :any:`numpy.ndarray` with the appropriate
        number of vectors
    """
    assert(n_vecs is not None)
    vec = np.asarray(vec)
    check_is_vector(vec)

    # Check done by reshape?
    l = vec.shape[0]
    remainder = l % n_vecs

    if remainder != 0:
        msg = "Vector with shape {} can not be split to {} # vectors: remainder {} (vec {})"
        logger.error(msg.format(shape, n_vecs, remainder, vec))
        msg = "Vector with shape {} can not be split to {} # vectors: remainder {}"
        raise Bact2AssertionError(msg.format(shape, n_vecs, remainder))

    n_elements = l // n_vecs
    n_shape = [n_vecs, n_elements]
    mat = np.reshape(vec, n_shape)
    return mat

def check_unset_elements(vec,  n_valid_rows = None, unset_elements_value = None):
    """Check that unset elements are really matching the expected value
    """
    assert(n_valid_rows is not None)
    assert(unset_elements_value is not None)

    check_is_vector(vec)

    l = vec.shape[0]

    if l < n_valid_rows:
        fmt = "vector has less elements {} than expected number of valid rows {} (vec {})"
        logger.error(fmt.format(l, n_valid_rows, vec))
        fmt = "vector has less elements {} than expected number of valid rows {}"
        raise Bact2AssertionError(fmt.format(l, n_valid_rows, vec))

    # Is that an off by one error?
    excess_elements = vec[n_valid_rows:]
    chk = excess_elements == unset_elements_value
    if not chk.all():
        fmt = "Not all excess elements matched the unset value: n_valid_rows {} vector shape {} expected value {} chk {} vector {}"
        logger.error(fmt.format(n_valid_rows, vec.shape, unset_elements_value, chk, vec))
        n_wrong_elements = np.sum(chk != True)
        fmt = "Not all excess elements matched the unset value: {} wrong?"
        raise Bact2ValueError(fmt.format(n_wrong_elements))

    return vec
