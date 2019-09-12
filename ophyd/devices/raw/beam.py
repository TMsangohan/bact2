from ophyd import Component as Cpt, Device, EpicsSignalRO, Signal
from ophyd import DerivedSignal
from ophyd.status import SubscriptionStatus

from bact.applib.lifetime.lifetime_calculate import fit_scaled_exp
from collections import deque

import numpy as np

class BeamCurrent( Device ):
    '''BESSY II beam current monitors

    BESSY II has three DCCT devices. The analog output is sent to
    different conversion devices.

    The three DCCT's are readable by the following parameters
        * cur1
        * cur2
        * cur2

    There are two variables that are attributed to topup
        * topup1
        * topup2

    Furthermore PTB has its own conversion devices:
        * ptb1, ptb

    '''
    cur1     = Cpt(EpicsSignalRO, 'CUMZD4R:rdCur', value = np.nan)
    cur2     = Cpt(EpicsSignalRO, 'CUMZD5R:rdCur', value = np.nan)
    cur3     = Cpt(EpicsSignalRO, 'CUMZT5R:rdCur', value = np.nan)

    topup1   = Cpt(EpicsSignalRO, 'TOPUP1T5G:rdCurrentR', value = np.nan)
    topup2   = Cpt(EpicsSignalRO, 'TOPUP2T5G:rdCurrentR', value = np.nan)

    ptb1 =  Cpt(EpicsSignalRO,'bIICurrent:Mnt1collectData.VALD', value = np.nan)
    ptb2 =  Cpt(EpicsSignalRO,'bIICurrent:Mnt2collectData.VALD', value = np.nan)

    readback = Cpt(EpicsSignalRO, 'TOPUPCC:rdCur', value = np.nan)

class BeamCurrentTriggered( BeamCurrent ):
    '''Beam currrent triggered by readback
    '''
    def trigger(self):

        def cb(**kwargs):
            return True
        stat = SubscriptionStatus(self.readback, cb, run=False)
        return stat
    
class Beam( Device ):
    """BESSY II Beam current.

    Currently it provides current reading
    """
    current = Cpt(BeamCurrent, #egu='mA',
                  #limits = (0, 5), settle_time = 1.0,
                  #timeout = 1.0,
    )


