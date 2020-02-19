import time
import numpy as np
import copy

from ophyd import EpicsSignalRO

_copy = copy.copy
class VectorSignalRO( EpicsSignalRO ):
    """
    Converts numpy array to pickle strings

    Currently only testing if databroker can handle a string.
    Instead of a pickle string it could return some handle to
    some database or filesystem

    Todo:
       Check if it should be more a proxy style class
    """
    def __init__(self, *args, **kws):
        super().__init__(*args, **kws)
        self._t0 = time.time()

    def read2(self, *args, **kws):
        """Convert a vector array to a pickle dump

        Will handle nearly any array. Implemented in
        a lazier fashion
        """
        r = super().read(*args, **kws)

        # Assuming that r contains exactly one entry
        res = {}
        for k, d in r.items():
            nd = _copy(d)
            for key, val in d.items():
                if type(val) == np.ndarray:
                    a_str = adapt_array(val)
                    nd[key] = a_str
                elif key == "timestamp":
                    dt = val - self._t0
                    # print("timestamp {}".format(dt))
            res[k] = nd
        return res

    def stop(self, *args, **kwargs):
        return super().stop(*args, **kwsargs)
