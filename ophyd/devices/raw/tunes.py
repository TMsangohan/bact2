from ophyd import Component as Cpt, Device, EpicsSignalRO, Signal
import numpy as np

class TuneMeasurement( Device ):
    '''BESSY II tunes
    TUNEZR:rdH -- 
    TUNEZR:rdV -- vertical tune from beam motion monitor
    SYNFREQZC:rdScope -- longitudinal tune from spectrum analyzer
    SYNFREQZC:rd -- longitudinal tune from bunch by bunch feedback
    BBQR:Z:PHTRK:FREQ -- longitudinal tune from phase tracking
    '''
    #: horizontal tune from beam motion monitor
    tunehor     = Cpt(EpicsSignalRO, 'TUNEZR:rdH', value = np.nan)
    tunever     = Cpt(EpicsSignalRO, 'TUNEZR:rdV', value = np.nan)

    #: longitudinal tune from spectrum analyzer
    tunelon     = Cpt(EpicsSignalRO, 'SYNFREQZC:rdScope', value = np.nan)

    
