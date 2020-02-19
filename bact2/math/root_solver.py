'''Root solver for functions defined by measurements

Typically usage:
    * :class:`CautiousRootSolver` as root solver
    * :class:`LinearGradient` as function evaluator


Warning:
    Work in progress. Requires to be tested using machine time
'''
import logging
import numpy as np
# from scipy.optimize import root_scalar
from scipy.optimize import newton
from dataclasses import dataclass

norm = np.linalg.norm
logger = logging.getLogger('bact2')


class LinearGradient:
    '''Gradient estimated on a linear fit from last data

    Args:
        func:           a function taking a value x and returning
                        a scalar a scalar value
        start_gradient: the gradient to be used during first function
                        evaluation
        scale_gradient: a scalar used to scale the computed gradient
                        with. This can be used to take artefacts of
                        `func` into account

    Keeps record of the last data. Computes the gradient making a
    linear interpolation to the last data retrieved.

    Typically used together with :class:`CautiousRootSolver`
    '''
    def __init__(self, func, start_gradient=1, scale_gradient=1):

        self.func = func
        self.x_vals = np.array([], np.float_)
        self.f_vals = np.array([], np.float_)
        self.scale_gradient = scale_gradient
        self.start_gradient = start_gradient

    @property
    def x(self):
        '''The stored x values (independents)
        '''
        x = np.asarray(self.x_vals)
        return x

    @property
    def f(self):
        '''The stored values the function returned (dependents)
        '''
        f = np.asarray(self.f_vals)
        return f

    def fdfFromInterpolation(self, x):
        '''Function value and its associated gradient from stored x and f

        Args:
            x: independent value

        Returns:
            f, df

        Makes a linear fit to the stored data x and f.
        Computes then the function value at the position x and
        its gradient based on the linear interpolation. Thus the gradient
        is equivalent to the slope of the interpolation line
        '''
        xv = self.x
        fv = self.f
        logger.info(f'Last data x={xv} f={fv}')
        p  = np.polyfit(xv, fv, 1)
        dp = np.polyder(p, 1)
        f  = np.polyval(p, x)
        df = np.polyval(dp, x)
        return f, df

    def df(self, x, f):
        '''Computes an estimate of the gradient

        If only one point is availabe, it will return
        the `start_gradient`. Otherwise it will used
        :meth:`fdfFromInterpolation` to compute the
        gradient.

        Todo:
            Remove `f` from argument
        '''
        if len(self.x_vals) < 2:
            df = self.start_gradient
        else:
            _, df = self.fdfFromInterpolation(x)
        return df * self.scale_gradient

    def __call__(self, x):

        f = self.func(x)
        self.x_vals = np.append(self.x_vals, x)
        self.f_vals = np.append(self.f_vals, f)

        df = self.df(x, f)
        logger.info(f"est x = {x:e} f = {f:e} df = {df:e}")
        return f, df


def length_of_points(xv, fv):
    '''Compute the length of line defined by extreme points

    Args:
        xv: x vector
        fv: f vector

    Returns:
        length of line described by extrama points of the points
        xv, fv

    Uses :func:`numpy.linalg.norm`

    Todo:
        Check computation.
    '''
    xv = np.asarray(xv)
    fv = np.asarray(fv)
    dx = xv.max() - xv.min()
    df = fv.max() - fv.min()
    return norm([dx, df])


@dataclass
class TestPointResult:
    '''Test point computed by :func:`compute_test_point`
    '''
    #: the test point computed
    result: float
    #: how much it is off from the already known points
    scale: float
    #: If true the test point is outside of the already known
    #: territory
    estimated: bool



def compute_test_point(xv, fv, x, f, df, max_scale=10):
    '''Acceptable based point based on linear extrapolation

    Computes a test point which is in direction of x,
    but its not further off than max_scale from the already
    known data. It assumes that the data xv and fv are
    basically representing a straight line.

    Args:
        xv: x vector containing previously collected data
        fv: f vector containing previously collected data

        x: value to probe
        f: expected function value at x
        df: expected gradient at x

        max_scale: maximum scale to accept for the next test point

    Returns:
        :class:`TestPointResult`

    This is computed in the following manner:
        1. Estimate current data span
            1. First the extrema are selected from xv and fv
            2. The distance between these points is used to represent
               the current scale
        2. Estimate how far off `x` and `f` are
            1. The extrema are again calculated adding `x` and `f` to the
               repective vectors
            2. Again the distance of these extrema is calculated
        3. the ratio of theses distances are used to calculate the scale
        4. If the scale is below max_scale the result is returned with
           the point identical to `x`.
        5. If the scale is out of range a point `x_estimate` is calculated
           using `max_scale`
    '''
    xtest = np.append(xv, x)
    ftest = np.append(fv, f)

    # compute overall distance of tracked points
    dl      = length_of_points(xv,    fv)
    dl_test = length_of_points(xtest, ftest)

    scale = dl_test / dl

    logger.info(
        f'xv {xv} x {x} dl {dl} dl_test {dl_test}'
        f' scale {scale} max scale {max_scale}'
    )

    if scale <= max_scale:
        # Not a decade off .. lets go ahead
        # That's the signal to the caller that no change
        # Was required
        r = TestPointResult(x, scale, False)
        return r

    # More than max_scale off: compute the test point ...
    dl_accepted = dl * max_scale

    # Only as much extrapolation as required
    # Should not really matter, but I tend to
    # favour a more stabler approach
    dl_extrapolate = dl_accepted - dl

    # per unit length in x dl is given bz
    dl_pu = norm([1, df])

    # Thus move in x
    dx_accepted = dl_extrapolate/dl_pu

    # The start point is the one in x closest to the requested point
    diff = x - xv
    adiff = np.absolute(diff)

    idx = adiff.argmin()
    x_start = xv[idx]
    # This is the distance from the nearest point in
    x_test = x_start + dx_accepted
    r = TestPointResult(x_test, scale, True)
    return r


class RootSolver:
    '''Solve root using newtons method

    Uses :func:`scipy.optimize.newton`. Used as base class
    for :class:`CautiousRootSolver`
    '''
    def __init__(self, func, x0=0):
        self.func = func
        self.x0 = x0

    def evalf(self, x):
        return self.func(x)

    def find_root(self):
        # r = root_scalar(self.evalf, x0=self.x0, fprime=True, xtol=.1, rtol=.1, method='newton')
        r = newton(self.evalf, x0=self.x0, fprime=True, xtol=.1, rtol=.1)
        return r


class CautiousRootSolver(RootSolver):
    '''A root solver cautiously extrapolating to unknwon x points

    Searches for a root of the function. Uses
    :func:`compute_test_point` to ensure that the next test point
    (or function evaluation) is not too far off from the area
    where measurements were already made.

    If points are too far off it will evaluate the function at the
    acceptable boundary and estimate the root point using the
    returned gradient. The property :any:`did_extrapolation`
    will then evaluate to `True`. It is the user's responsibility
    to decide if further evaluations are required.

    Restarting the search for the root calling :meth:`find_root`
    with the returned x will get closer to the actual root.



    Args:
        func: A instance of a callable class that stores the
              values that were called last. See
              :class:`LinearGradient` for an implemementation
              example

        x0: Start point to search for the root

    Use :meth:`find_root` to start the computation of the root.

    Todo:

       *  make `max_scale` an argument of class instantiation


    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._did_extrapolation = False

    @property
    def did_extrapolation(self):
        '''Is the root returned based on extrapolation
        '''
        return self._did_extrapolation

    def find_root(self):
        return super().find_root()

    def evalf(self, x):
        xv = self.func.x
        fv = self.func.f

        if len(xv) < 2:
            return self.func(x)

        # Now the extrapolation has to be calculated
        f_forecast, df_forecast = self.func.fdfFromInterpolation(x)

        # How far are we off from the interpolation range ...
        r = compute_test_point(xv, fv, x, f_forecast, df_forecast)
        if not r.estimated:
            self._did_extrapolation = False
            # r.result should be identical to x
            return self.func(r.result)
        else:
            self._did_extrapolation = True

        f_test = self.func(r.result)
        # Extrapolate to the correct point
        dx = x - r.result
        f_extrapolated = f_test + df_forecast * dx
        return f_extrapolated
