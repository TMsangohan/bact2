from ophyd import Component as Cpt, Device, EpicsSignalRO, Signal
from ophyd.device import DynamicDeviceComponent as DDC
from ophyd.areadetector.base import ad_group

from .bpm_config import bpm_conf


class BPMSingleChannel( Device ) :
    
    _default_config_attrs = ('state', 'scale')
    
    state = Cpt(Signal, name = 'state', default = False)
    scale = Cpt(Signal, name = 'scale', default = False)

    
class BPMSingleChannelX( BPMSingleChannel ):
    pos = Cpt(EpicsSignalRO, 'rdX')
    sig = Cpt(EpicsSignalRO, 'rdSigX')

class BPMSingleChannelX( BPMSingleChannel ):
    pos = Cpt(EpicsSignalRO, 'rdY')
    sig = Cpt(EpicsSignalRO, 'rdSigY')
    
class BPMSingle( Device ):
    
    x      = Cpt(BPMSingleChannelX, 'x')
    y      = Cpt(BPMSingleChannelX, 'y')
    
    cross  = Cpt(EpicsSignalRO, 'rdZsum')
    sum    = Cpt(EpicsSignalRO, 'rdAgc')
    status = Cpt(EpicsSignalRO, 'rdStatus')


all_bpms = [(entry[0].lower(), entry[0]) for entry in bpm_conf]

class BPMCollection( Device ):
    col = DDC(ad_group(BPMSingle, all_bpms),
              doc='all bpms',
              default_read_attrs = (),
    )
    print(col)
    pass

def main():
    col = BPMCollection(name = 'test')

if __name__ == '__main__':
    main()
