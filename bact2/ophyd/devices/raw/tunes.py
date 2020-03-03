from ophyd import Component as Cpt, Device, EpicsSignalRO, Signal
from ophyd.status import SubscriptionStatus, AndStatus

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

class TuneSpectrumRawChannel( Device):
    '''raw spectrum

    These spectra are stored in the fast archiver but not in the standard one.
    Trigger returns when new data are available

    Please note the sel
    '''
    #: raw data preprocessed by (data reduction in time)
    #: direct access to raw data available if one removes the underscore
    spec = Cpt(EpicsSignalRO, ':wavetuneALL_')
    # raw access to the data
    spec = Cpt(EpicsSignalRO, ':wavetuneALL')
    #: resolution of the waveform
    resolution = Cpt(EpicsSignalRO, ':wavetuneALL_.XRES')
    #: data should arrive at least everz 10 seconds. 
    timeout = Cpt(Signal, name = 'timeout', value=10 * 1.5)
    
    _default_configuration_attrs = ('timeout', 'resolution')
     
    def trigger(self):
        def cb(**kwargs):
            """Wait for new data

            If this data is here we are done ...
            All this nice checks do not work
            """
            return True

        timeout = self.timeout.value
        stat = SubscriptionStatus(self.spec, cb, timeout=timeout, run=False)
        return stat

class TuneSpectrumRaw( Device):
    ch1 = Cpt(TuneSpectrumRawChannel, 'pxi1zs12g', name = 'ch1')
    ch2 = Cpt(TuneSpectrumRawChannel, 'pxi2zs12g', name = 'ch2')

    def trigger(self):
        # stat1 = self.ch1.trigger()
        stat2 = self.ch2.trigger()
        #stat = AndStatus(stat1, stat2)
        return stat2

        
        
class TuneMeasurement( Device ):
    '''BESSY II tunes

       * SYNFREQZC:rdScope -- longitudinal tune from spectrum analyzer
       * SYNFREQZC:rd      -- longitudinal tune from bunch by bunch feedback
    '''

    bpm = Cpt(TunesFromBPM, name='bpm')
    bbfb = Cpt(TuneFromBBFB, 'BBQR', name='bbfb')

    #: longitudinal tune from spectrum analyzer
    longitudinal = Cpt(EpicsSignalRO, 'SYNFREQZC:rdScope', value = np.nan)
