from ophyd import Component as Cpt, Device, EpicsSignalRO, Signal

class Bookkeeping( Device ):
    mode = Cpt(Signal, name = 'mode', value = 'unknown')
    scale_factor  = Cpt(Signal, name = 'scale_factor', value = 1.0)
    current_offset = Cpt(Signal, name = 'current_offset', value = 0.0)
    dI = Cpt(Signal, name = 'dI', value = 0.0)
    steerer_name = Cpt(Signal, name = 'steerer_name', value = 'unknown')
