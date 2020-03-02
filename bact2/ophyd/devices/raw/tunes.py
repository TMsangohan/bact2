from ophyd import Component as Cpt, Device, EpicsSignalRO, Signal
import numpy as np

class TunesFromBPM( Device ):
    '''
    Following tune variables are available:
       * TUNEZR:rdH        -- horiyontal tune from beam motion monitor
       * TUNEZR:rdV        -- vertical tune from beam motion monitor
    '''
    #: horizontal tune from beam motion monitor
    horizontal  = Cpt(EpicsSignalRO, 'TUNEZR:rdH', value = np.nan)
    vertical    = Cpt(EpicsSignalRO, 'TUNEZR:rdV', value = np.nan)


class TuneFromBBFBTau( Device ):
    '''
    '''
    peak_q1 = Cpt(EpicsSignalRO, ':PEAKFREQ1', value = np.nan)
    peak_q2 = Cpt(EpicsSignalRO, ':PEAKFREQ2', value = np.nan)

class TuneFromBBFBCoor( Device ):
    '''
    '''
    short = Cpt(TuneFromBBFBTau, ':BRAM')
    long = Cpt(TuneFromBBFBTau,  ':SRAM')
    sb = Cpt(EpicsSignalRO, ':SB:PEAKFREQ1')
    phtrk = Cpt(EpicsSignalRO, ':PHTRK:FREQ')

class TuneFromBBFB( Device ):
    x = Cpt(TuneFromBBFBCoor, ':X')
    y = Cpt(TuneFromBBFBCoor, ':Y')
    z = Cpt(TuneFromBBFBCoor, ':Z')

class TuneMeasurement( Device ):
    '''BESSY II tunes

       * SYNFREQZC:rdScope -- longitudinal tune from spectrum analyzer
       * SYNFREQZC:rd      -- longitudinal tune from bunch by bunch feedback
    '''

    bpm = Cpt(TunesFromBPM, name='bpm')
    bbfb = Cpt(TuneFromBBFB, 'BBQR', name='bbfb')

    #: longitudinal tune from spectrum analyzer
    longitudinal = Cpt(EpicsSignalRO, 'SYNFREQZC:rdScope', value = np.nan)
