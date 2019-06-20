from ophyd import Signal, Device, Component as Cpt
from ophyd.areadetector.base import ad_group
from ophyd.device import  DynamicDeviceComponent as DDC
from ophyd.status import Status

from .power_converter import PowerConverter
from .steerer_list import horizontal_steerers, vertical_steerers
from collections import OrderedDict
import numpy as np
import string
import logging

logger = logging.getLogger()

class Steerer( Device ):
    """Steerer with certain settings
    """
    dev = Cpt(PowerConverter, '', egu='A',
              #setting_parameters = 0.1,
              settle_time = 1e-2 # 10 ms
              timeout = 2)


all_steerers = horizontal_steerers + vertical_steerers
t_steerers = [(name.lower(), name) for name in all_steerers]


class SignalHelper( Signal ):
    def set_cb(args, **kwargs):
        # fmt = "set_cb args {} kwargs {}"
        # print(fmt.format(args, kwargs))
        value = kwargs["value"]
        return super().set(value)

    def trigger(self):
        return self.parent.selected_steerer.trigger()

    def read(self):
        return self.parent.selected_steerer.read()


class SteererCollection( Device ):
    steerers = DDC(ad_group(Steerer, t_steerers),
        doc='all steerers',
              default_read_attrs = (),
    )

    selected = Cpt(Signal, name='selected', value ='non selected')
    sel_setpoint = Cpt(SignalHelper, name='sel_setpoint', value = np.nan)
    sel_readback = Cpt(SignalHelper, name='sel_readback', value = np.nan)



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected_steerer = None
        self.__logger = logger

    @property
    def selected_steerer(self):
        sel = self._selected_steerer
        if sel is None:
            raise AssertionError('No steerer was selected!')

        print("Selected steerer {}".format(sel))
        return sel

    def unsubscribeSelected(self):
        if self._selected_steerer is not None:
            sel = self._selected_steerer.dev
            sel.setpoint.clear_sub(self.sel_setpoint.set_cb)
            sel.readback.clear_sub(self.sel_readback.set_cb)
            self._selected_steerer = None

    def __del__(self):
        self.unsubscribeSelected()

    def subscribeSelected(self):
        sel = self._selected_steerer.dev
        sel.setpoint.subscribe(self.sel_setpoint.set_cb)
        sel.readback.subscribe(self.sel_readback.set_cb)


    def setLogger(self, logger):
        self.__logger = logger

    def set(self, name):
        """Just to make it easier to run it with bluesky

        Args:
            name : steerer name
        """

        self.unsubscribeSelected()
        steerer = getattr(self.steerers, name)
        self.__logger.debug("Selected steerer {}".format(steerer))
        self._selected_steerer = steerer

        status = self.selected.set(name)

        def install_cb():
            self.subscribeSelected()

        status.add_callback(install_cb)
        return status
