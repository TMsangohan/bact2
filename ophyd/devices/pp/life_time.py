from bact.applib.lifetime.lifetime_calculate import fit_scaled_exp
from ..raw.beam import BeamCurrent
from ophyd import Component as Cpt, Device, EpicsSignalRO, Signal

import numpy as np
from collections import deque


class LifetimeSignal( Device ):
    current_readings = Cpt(Signal, name = 'currents',     value = [])
    min_readings     = Cpt(Signal, name = 'min_readings', value = 8)

    readings_to_sum  = Cpt(Signal, name = 'readings_to_sum', value = 10)
    
    lt     = Cpt(Signal, name = 'lifetime',       value = np.nan)
    lt_err = Cpt(Signal, name = 'lifetime_error', value = np.nan)

    _default_config_attrs = ('readings_to_sum', 'min_readings')

    def __init__(self, *args, current_signal_name = None, parent = None, **kwargs):
        super().__init__(*args, parent = parent, **kwargs)
        current_signal = getattr(parent, current_signal_name)
        self.current_signal = current_signal
        self.current_readings_raw = None

    def resetCurrentReadings(self):
        maxlen = self.readings_to_sum.value
        self.current_readings_raw = deque(maxlen = maxlen)
        self.current_readings.value = []

    def addCurrentReading(self):
        '''
        Todo:
           update lifetime and lifetime error
        '''

        rdbk = self.current_signal.readback
        value = rdbk.value
        timestamp = rdbk.timestamp
        
        check = rdbk.read()

        a = np.array([timestamp, value])
        # print('Adding reading t = {0[0]} v = {0[1]} check{1}'.format(a, check))
        # print('Adding reading t = {0[0]} v = {0[1]}'.format(a))
        self.current_readings_raw.append(a)
        self.current_readings.value = np.array(self.current_readings_raw)

        self.calculateLifetime()


    def calculateLifetime(self):

        data = np.array(self.current_readings.value)
        if data.shape[0] < self.min_readings.value:
            self.lt.put(np.nan)
            self.lt_err.put(np.nan)
            return

        t0 = data[0,0]

        dt = data[:,0] - t0
        dc = data[:,1]

        c, cov, err = fit_scaled_exp(dt, dc)
        sec_to_hour = 1./(60. * 60)
        lt = c[1] * sec_to_hour
        lt_err = err[1] * sec_to_hour

        lt = lt * (-1)
        self.log.debug('t {} c{} -> returning c {} c_err {}'.format(dt, dc, c, err))
        # print('lt {} lt_err {}'.format(lt, lt_err))

        self.lt.put(lt)
        self.lt_err.put(lt_err)


    def trigger(self):
        def update():
            self.addCurrentReading()

        stat = self.current_signal.trigger()
        stat.add_callback(update)
        return stat


    def stage(self):
        r = super().stage()
        self.resetCurrentReadings()
        return r

    def suspend(self):
        '''

        Todo:
           Check if called by run engine!
        '''
        r = super.suspend()
        self.resetCurrentReadings()
        return r

    def resume(self):
        '''

        Todo:
           Check if called by run engine!
        '''
        # r = super.resume()
        self.resetCurrentReadings()
        # return r



class LifetimeDevice( Device ):
    beam_current = Cpt(BeamCurrent, name = 'beam_current')
    life_time = Cpt(LifetimeSignal, name = 'life_time',  current_signal_name = 'beam_current')

    def trigger(self):
        return self.life_time.trigger()

    def suspend(self):
        return self.life_time.suspend()

    def resume(self):
        return self.life_time.resume()

    def stop(self):
        return self.life_time.stop()
