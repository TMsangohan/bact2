from ophyd import Component as Cpt, Device, PVPositionerPC, PVPositioner
from ophyd import EpicsSignal, EpicsSignalRO

class LinacGun( Device ):
    '''
    '''
    timer_gun_pulses = Cpt(EpicsSignalRO, 'LINAC1C:setTB_GPN')
