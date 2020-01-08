'''Main Ring Power RF amplifiers

Operated at roughly 500 MHz.
'''
from ophyd import Component as Cpt, Device, Signal
from ophyd import EpicsSignalRO, EpicsSignal, PVPositionerPC


class RFAmplifier(Device):
    '''One RF Amplifier

    Todo:
       Convert it to a PCPostioner...
    '''
    readback = Cpt(EpicsSignalRO, ':Ctrl:rdCavVolt')
    setpoint = Cpt(EpicsSignal,   ':sCavSet')

    
class RFAmplifiersCombined(PVPositionerPC):
    '''
    '''
    setpoint = Cpt(EpicsSignal, ':sCavSet')
    readback = Cpt(EpicsSignal, ':sCavSet')
    mode     = Cpt(EpicsSignalRO, ':mode')

    def stage(self):
        '''Check if setting the common device is permitted
        '''
        l = super().stage()

        fmt = '{}:{} stage mode + {}'
        txt = fmt.format(__name__, self.__class__.__name__, self.mode)
        self.log.debug(txt)

        permitted = self.mode.value == 1
        if not permitted:
            raise AssertionError('Cavity collection is not enabled')

        r = l + [self]
        return r

    
class RFAmplifiers(Device):
    '''
    '''
    amp_1 = Cpt(RFAmplifier, 'PAH1R')
    amp_2 = Cpt(RFAmplifier, 'PAH2R')
    amp_3 = Cpt(RFAmplifier, 'PAH3R')
    amp_4 = Cpt(RFAmplifier, 'PAH4R')

    col = Cpt(RFAmplifiersCombined, 'PAHR', settle_time = 5)
