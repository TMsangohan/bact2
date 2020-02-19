from ophyd import Component as Cpt, Signal
from ophyd import Device

import time
import numpy as np



    
class TimeStats:
    """Create stats of time
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        now = time.time()
        self._t0 = now
        self._t1 = now -1
        


    def tic(self):
        self._t0 = time.time() 
        
    def tac(self):
        self._t1 = time.time() 
        

    def read(self):
        dt = self._t1 - self._t0
        return dt
    
