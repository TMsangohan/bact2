'''Booster feedback
'''
from ophyd import Component as Cpt, Device, EpicsSignal, EpicsSignalRO
from ophyd.status import AndStatus

class BoosterFeedbackX( Device ):
    '''
    '''
    active = Cpt(EpicsSignal,   'BBQB:X:FBCTRL')
    state  = Cpt(EpicsSignalRO, 'TFBAXQS7G:stStat')

class BoosterFeedbackY( Device ):
    '''
    '''
    active = Cpt(EpicsSignal,   'BBQB:Y:FBCTRL')
    state  = Cpt(EpicsSignalRO, 'TFBAYQS7G:stStat')

class BoosterFeedbackZ( Device ):
    '''
    '''
    active = Cpt(EpicsSignal,   'BBQB:Z:FBCTRL')
    state  = Cpt(EpicsSignalRO, 'LFBAQS7G:stStat')

class BoosterFeedbackS( Device ):
    '''
    '''
    active = Cpt(EpicsSignal,   'BBQB:S:FBCTRL')


class BoosterFeedback( Device ):
    x = Cpt(BoosterFeedbackX, name = 'x')
    y = Cpt(BoosterFeedbackY, name = 'y')
    z = Cpt(BoosterFeedbackZ, name = 'z')
    s = Cpt(BoosterFeedbackZ, name = 's')


    def set(self, val):
        stat_x = self.x.active.set(val)
        stat_z = self.z.active.set(val)
        stat1 = AndStatus(stat_x, stat_z)

        # stat_y = self.y.active.set(val)
        # stat_s = self.s.active.set(val)
        # stat2 = AndStatus(stat_y, stat_s)
        # stat = AndStatus(stat1, stat2)

        return stat1
