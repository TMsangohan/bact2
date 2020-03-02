from ophyd import Component as Cpt, Device, PVPositionerPC, PVPositioner
from ophyd import EpicsSignal, EpicsSignalRO

class TopUpEngine( Device ):    
    next_injection = Cpt(EpicsSignalRO, "TOPUPCC:estCntDwnS")
    
    #: Bunch extracted from booster synchrotron to machine
    injection_trigger = Cpt(EpicsSignalRO, 'TOPUPCC:stTrg')

    #: Number of bunches
    number_of_bunches = Cpt(EpicsSignal, 'TOPUPCC:setMaxNrBunches')

    next_injection = Cpt(EpicsSignalRO, 'TOPUPCC:estCntDwnS')
