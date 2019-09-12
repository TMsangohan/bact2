from ophyd import Component as Cpt, Device, EpicsSignalRO


class LifeTime( Device ):
    '''BESSY II Lifetime estimate

    '''
    #: ten seconds average
    life_time_10 = Cpt(EpicsSignalRO, 'CUMZD4R:rdLt10')


