from ophyd import Component as Cpt, Device, PVPositionerPC, PVPositioner
from ophyd import EpicsSignal, EpicsSignalRO

class TopUpEngine( Device ):    
    next_injection = Cpt(EpicsSignalRO, "TOPUPCC:estCntDwnS")
