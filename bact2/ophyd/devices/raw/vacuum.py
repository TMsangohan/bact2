from ophyd import Component as Cpt, Device, EpicsSignalRO

class VacuumSensor( Device ):
    pressure = Cpt(EpicsSignalRO, ':rdPress')
    quality  = Cpt(EpicsSignalRO, ':stMeasQuality')
    
