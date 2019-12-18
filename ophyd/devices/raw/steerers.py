'''Steerer collection and steerer as multiplexer

Todo:
   * Implement stop / resume method. When the program is stopped
     by the user, the steerer should finish the hysteresis loop



'''
from ophyd import Signal, Device, Component as Cpt
from ophyd.areadetector.base import ad_group
from ophyd.device import  DynamicDeviceComponent as DDC
from ophyd.status import AndStatus

from .power_converter import PowerConverter
from ..utils import trigger_on_update
from .steerer_list import horizontal_steerers, vertical_steerers
import numpy as np

import logging
logger = logging.getLogger('bact2')

all_steerers = horizontal_steerers + vertical_steerers
t_steerers = [(name.lower(), name) for name in all_steerers]

horizontal_steerer_names = [name.lower() for name in horizontal_steerers]
vertical_steerer_names   = [name.lower() for name in vertical_steerers]



class SignalProxy( Signal ):
    """Proxy the signal to a
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__signal_to_proxy = None

    @property
    def signal_to_proxy(self):
        if self.__signal_to_proxy is None:
            raise AssertionError("No signal to proxy found in {}".format(self.name))
        return self.__signal_to_proxy

    @signal_to_proxy.setter
    def signal_to_proxy(self, sig):
        assert(callable(sig.set))
        assert(callable(sig.read))
        assert(callable(sig.trigger))
        if not sig.connected:
            sig.wait_for_connection()
        self.__signal_to_proxy = sig

    def remove_proxy_signal(self):
        self.__signal_to_proxy = None


    def set(self, *args, **kwargs):
        sig = self.signal_to_proxy
        return sig.set(*args, **kwargs)

    def get(self, *args, **kwargs):
        sig = self.signal_to_proxy
        return sig.get(*args, **kwargs)

    def trigger(self):
        sig = self.signal_to_proxy
        status = sig.trigger()
        self.log.debug("{}.trigger returns {}".format(self.name, status))
        return status

    def read(self):
        """Substituting the name with the proxy name
        """
        sig = self.signal_to_proxy
        proxy_name = self.signal_to_proxy.name
        # print(proxy_name, self.name)
        r = sig.read()
        d = {}
        # It is essential not to return the data also for the selected steerer
        # as the database will choke afterwards as it can not find the names
        for key, item in r.items():
            if key == proxy_name:
                key2 = self.name
                d[key2] = item
            else:
                d[key] = item
        fmt = "{}.read returns {}"
        self.log.debug(fmt.format(self.name, d))
        return d

    #def __getattr__(self, name):
    #    print("Getting name", name)
    #    return getattr(self.signal_to_proxy, name)


class Steerer( PowerConverter ):
    """Steerer with certain settings
    """
    def __init__(self, *args, **kwargs):
        # could be 10 ms enough?
        kwargs.setdefault('settle_time', 0.1)
        super().__init__(*args, **kwargs)


class _SelectedSteerer( Device ):
    setpoint = Cpt(SignalProxy, name='set',  value = np.nan, kind = 'hinted', lazy = False)
    readback = Cpt(SignalProxy, name='rdbk', value = np.nan, kind = 'hinted', lazy = False)

    def __init__(self, *args, **kwargs):
        self._selected_steerer = None
        super().__init__(*args, **kwargs)

    def subscribeSelected(self):
        self.setpoint.signal_to_proxy = self.selected_steerer.setpoint
        self.readback.signal_to_proxy = self.selected_steerer.readback

    def unsubscribeSelected(self):
        if self._selected_steerer is not None:
            self._selected_steerer = None
        self.setpoint.remove_proxy_signal()
        self.readback.remove_proxy_signal()

    @property
    def selected_steerer(self):
        sel = self._selected_steerer
        if sel is None:
            raise AssertionError('No steerer was selected!')

        self.log.info("Selected steerer {}".format(sel))
        return sel

    def setSteerer(self, steerer):
        self.unsubscribeSelected()
        self._selected_steerer = steerer
        self.subscribeSelected()


    def trigger(self):
        st_set = self.setpoint.trigger()
        st_rbk = self.readback.trigger()
        status = AndStatus(st_set, st_rbk)
        return status


    def read(self):
        r = super().read()
        tup = self.__class__.__name__, __name__, r
        txt = '{}:{}.read() returns = {}'.format(*tup)
        self.log.debug(txt)
        return r

    def __del__(self):
        self.unsubscribeSelected()

class SelectedSteerer( Device ):
    """Pass it through ...
    """
    dev = Cpt(_SelectedSteerer, '', #egu='A',
              #setting_parameters = 0.1,
              #timeout = 2
                  )

    def trigger(self):
        return self.dev.trigger()


class SteererCollection( Device ):
    steerers = DDC(ad_group(Steerer, t_steerers),
        doc='all steerers',
              default_read_attrs = (),
    )

    selected = Cpt(Signal, name='selected', value ='none selected')
    sel = Cpt(SelectedSteerer, name = 'sel_st')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setDefaultSteerer()


    def _setDefaultSteerer(self):
        self._setSteererByName(t_steerers[0][0])


    def _setSteererByName(self, name):
        try:
            steerer = getattr(self.steerers, name)
            self.sel.dev.setSteerer(steerer)
        except Exception as e:
            fmt = "{}._setSteererByName failed to set steerer {} reason {}"
            self.log.error(fmt.format(self.name, name, e))
            raise
        self.log.info("Selected steerer {}".format(steerer))

    def set(self, name):
        """Just to make it easier to run it with bluesky

        Args:
            name : steerer name
        """
        self.log.info("Selecting steerer {}".format(name))
        self._setSteererByName(name)
        t_name = str(name)
        status = self.selected.set(t_name)
        return status


    def trigger_all_components_update(self):
        status = None
        for name in self.steerers.component_names:
            cpt = getattr(self.steerers, name)
            sig_rdbk = cpt.readback
            r = trigger_on_update(sig_rdbk)
            if status == None:
                status = r
            else:
                status = AndStatus(status, r)
        return status

    def trigger(self):
        status = self.sel.trigger()
        fmt = "{}.trigger: {} "
        self.log.debug(fmt.format(self.name, status))
        return status
