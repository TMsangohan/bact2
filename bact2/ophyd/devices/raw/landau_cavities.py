from ophyd import Component as Cpt, Device, EpicsSignalRO, Signal
# from ophyd import DerivedSignal
# from ophyd.status import SubscriptionStatus



resultcolumns=[
    'CUMZD4R:rdCur','CUMZD5R:rdCur','CUMZT5R:rdCur',

    'BBQR:Z:SRAM:MEAN','CUMZR:MBcurrent',
]

class LandauCavity(Device):
    '''One landau cavity
    '''
    hf_voltage = Cpt(EpicsSignalRO, ':hfv:rdbk')
    power      = Cpt(EpicsSignalRO, ':power:rdbk')

class LandauCavities(Device):
    '''Landau cavities 4 piecies for us
    '''
    
    cav_1 = Cpt(LandauCavity, 'LC1HT1R')
    cav_2 = Cpt(LandauCavity, 'LC2HT1R')
    cav_3 = Cpt(LandauCavity, 'LC3HT1R')
    cav_4 = Cpt(LandauCavity, 'LC4HT1R')
