import numpy as np
from scipy.optimize import root_scalar

norm = np.linalg.norm


class LinearGradient:
    '''Gradient estimated linearly from last data
    '''
    def __init__(self, func, start_gradient = 1, scale_gradient = 1):

        self.func = func
        self.x_vals = np.array([], np.float_)
        self.f_vals = np.array([], np.float_)
        self.scale_gradient = scale_gradient
        self.start_gradient = start_gradient

    @property
    def x(self):
        x = np.asarray(self.x_vals)
        return x

    @property
    def f(self):
        f = np.asarray(self.f_vals)
        return f

    def fdfFromInterpolation(self, x):
        xv = self.x
        fv = self.f
        print(f'Last data x={xv} f={fv}')
        p  = np.polyfit(xv, fv, 1)
        dp = np.polyder(p, 1)
        f  = np.polyval(p, x)
        df = np.polyval(dp, x)
        return f, df

    def df(self, x, f):
        if len(self.x_vals) < 2:
            df = self.start_gradient
        else:
            _, df = self.fdfFromInterpolation(x)
        return df * self.scale_gradient

    def __call__(self, x):

        f =  self.func(x)
        self.x_vals = np.append(self.x_vals, x)
        self.f_vals = np.append(self.f_vals, f)

        df = self.df(x,f)
        print(f"est x = {x:e} f = {f:e} df = {df:e}")
        return f, df


def length_of_points(xv, fv):
    '''Compute the length of straight from start to end point

    Args:
        xv: x vector
        fv: f vector

    Returns:
        length of line described by extrama points of the points
        xv, fv

    Uses :func:`norm`
    '''
    xv = np.asarray(xv)
    fv = np.asarray(fv)
    dx = xv.max() - xv.min()
    df = fv.max() - fv.min()
    return norm([dx, df])


class TestPointResult():
    __slots__ = ['result', 'scale', 'estimated']
    def __init__(self, result, scale, estimated):
        self.result = float(result)
        self.scale = float(scale)
        self.estimated = bool(estimated)


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
    dl_test = length_of_points(xtest, fv)

    scale = dl_test / dl

    print(f'xv {xv} x {x} dl {dl} dl_test {dl_test} scale {scale} max scale {max_scale}')
    if scale <= max_scale:
        # Not a decade off .. lets go ahead
        # That's the signal to the caller that no change
        # Was required
        r = TestPointResult(x, scale, False)
        return r

    # More than a decade off: compute the test point ...
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


class RootFinder:
    def __init__(self, func, x0=0):
        self.func = func
        self.x0 = x0

    def evalf(self, x):
        return self.func(x)

    def find_root(self):
        r = root_scalar(self.evalf, x0=self.x0, fprime=True, xtol=.1, rtol=.1, method='newton')
        return r


class CautiousRootFinder(RootFinder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._did_extrapolation = False

    @property
    def did_extrapolation(self):
        return self._did_extrapolation

    def find_root(self):
        return super().find_root()

    def evalf(self, x):
        xv = self.func.x
        fv = self.func.f

        if len(xv)<2:
            return self.func(x)

        # Now the extrapolation has to be calculated
        f_forecast, df_forecast = self.func.fdfFromInterpolation(x)

        # How far are we off from the interpolation range ...
        r = compute_test_point(xv, fv, x, f_forecast, df_forecast)
        if not r.estimated:
            # point x can be used ...
            return self.func(r.result)

        f_test = self.func(r.result)

        # Extrapolate to the correct point
        dx = x - r.result
        f_extrapolated = f_test + df_forecast * dx

        return f_extrapolated
