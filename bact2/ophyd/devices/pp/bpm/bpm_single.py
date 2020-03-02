'''Access every single beam position monitor as an separate device

BESSY II Beam position monitors are read out by a collector IOC.
The access to this IOC is wrapped in
:mod:`bact2.ophyd.devices.pp.bpm`. This implementation should be
the first solution stop.
'''
from ophyd import Component as Cpt, FormattedComponent as FC, Device, EpicsSignalRO, Signal
from ophyd.device import DynamicDeviceComponent as DDC
from ophyd.areadetector.base import ad_group

from .bpm_config import bpm_conf


class BPMSingleChannel( Device ) :
    '''One coordinate of the beam position monitor
    '''

    _default_configuration_attrs = ('state', 'scale')

    state = Cpt(Signal, name = ':state', value = False)
    scale = Cpt(Signal, name = ':scale', value = False)
    pos   = FC(EpicsSignalRO, '{self.prefix}:rd{self._coor_name}')
    sig   = FC(EpicsSignalRO, '{self.prefix}:rdSig{self._coor_name}')

    def __init__(self, prefix, coordinate_name=None, **kwargs):
        self._coor_name = coordinate_name
        super().__init__(prefix, **kwargs)


class BPMSingle( Device ):
    '''Single device access

    Signal device components derived from BPM.

    Todo:
        Implement triggering
    '''
    x      = Cpt(BPMSingleChannel, suffix = '', coordinate_name = 'X')
    y      = Cpt(BPMSingleChannel, suffix = '', coordinate_name = 'Y')


    sum    = Cpt(EpicsSignalRO, ':rdAgc')
    cross  = Cpt(EpicsSignalRO, ':rdZSum')
    status = Cpt(EpicsSignalRO, ':rdStatus')


all_bpms = [(entry[0].lower(), entry[0]) for entry in bpm_conf]

class BPMCollection( Device ):

    col = DDC(ad_group(BPMSingle, all_bpms),
              doc='all bpms',
              default_read_attrs = (),
    )

class BPMCollectionForComparison( BPMCollection ):
    x = Cpt(Signal, name = 'col_x', value = [])
    y = Cpt(Signal, name = 'col_y', value = [])
    names = Cpt(Signal, name = 'names', value = [])

    _default_configuration_attrs = ('names',)
    _default_read_attrs = ('x', 'y')

    def updateCollections(self):
        # First put the readings into col x and y ...
        x = []
        y = []
        for name in self.names.value:
            dev = getattr(self.col, name)
            x.append(dev.x.pos.value)
            y.append(dev.y.pos.value)

        # print("Putting x {}".format(x))
        self.x.put(x)
        self.y.put(y)

    def trigger(self):
        '''
        '''
        stat =  super().trigger()
        stat.add_callback(self.updateCollections)
        return stat
