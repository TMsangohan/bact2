from ophyd import Signal, Device, Component as Cpt
from ophyd.areadetector.base import ad_group
from ophyd.device import  DynamicDeviceComponent as DDC
from ophyd.status import Status

from .power_converter import PowerConverter
from .steerer_list import horizontal_steerers, vertical_steerers
from collections import OrderedDict
import string

class Steerer( Device ):
    """Steerer with certain settings
    """
    dev = Cpt(PowerConverter, '', egu='A', setting_parameters = 0.1,  timeout = 2)


all_steerers = horizontal_steerers + vertical_steerers
t_steerers = [(name.lower(), name) for name in all_steerers]

class SteererCollection( Device ):
    steerers = DDC(ad_group(Steerer, t_steerers),
        doc='all steerers',
              default_read_attrs = (),
    )

    selected = Cpt(Signal, name='selected', value ='non selected')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected_steerer = None

    @property
    def selected_steerer(self):
        sel = self._selected_steerer
        if sel is None:
            raise AssertionError('No steerer was selected!')

        print("Selected steerer {}".format(sel))
        return sel

    def set(self, name):
        """Just to make it easier to run it with bluesky

        Args:
            name : steerer name
        """
        self._selected_steerer = None
        steerer = getattr(self.steerers, name)
        self._selected_steerer = steerer

        status = self.selected.set(name)
        return status
