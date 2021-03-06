'''Steerer collection and steerer as multiplexer

Todo:
   * Implement stop / resume method. When the program is stopped
     by the user, the steerer should finish the hysteresis loop



'''
from ophyd import Signal, Device, Component as Cpt, Kind
from ophyd.areadetector.base import ad_group
from ophyd.device import DynamicDeviceComponent as DDC
from ophyd.status import AndStatus

from .power_converter import PowerConverter
from ..utils import trigger_on_update
from .steerer_list import horizontal_steerers, vertical_steerers
import numpy as np

import logging
logger = logging.getLogger('bact2')

all_steerers = horizontal_steerers + vertical_steerers
t_steerers = [(name.lower(), name) for name in all_steerers]
t_steerer_names = [entry[0] for entry in t_steerers]

horizontal_steerer_names = [name.lower() for name in horizontal_steerers]
vertical_steerer_names   = [name.lower() for name in vertical_steerers]


class SignalProxy(Signal):
    """Proxy the signal to a
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__signal_to_proxy = None

    @property
    def signal_to_proxy(self):
        if self.__signal_to_proxy is None:
            txt = f"No signal to proxy found in {self.name}"
            raise AssertionError(txt)
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

    @property
    def limits(self):
        return self.signal_to_proxy.limits

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


class Steerer(PowerConverter):
    """Steerer with certain settings
    """

    #: reference value to store
    rv = Cpt(Signal, name='ref_val', value=np.nan)

    #: shall the component be set back
    set_back = Cpt(Signal, name='set_bak', value=False, kind=Kind.config)

    #: acceptable relative error
    eps_rel = Cpt(Signal, name='eps_rel', value=2e-3)

    #: execution stopped with a difference of 0.7 %
    #: at a value of 0.13
    eps_abs = Cpt(Signal, name='eps_abs', value=1e-2)

    def __init__(self, *args, **kwargs):
        # 10 ms is way too short
        # let's go for rather half a second
        kwargs.setdefault('settle_time', .5)
        kwargs.setdefault('timeout', 20)
        super().__init__(*args, **kwargs)

    def setToStoredValue(self):
        if self.set_back.value:
            self.setpoint.value = self.rv.value

    def stage(self):
        '''
        '''
        self.rv.value = self.setpoint.value
        return super().stage()

    def unstage(self):
        '''

        Warning:
            If the call to super is not here proper plans will stop
            working at the second iteration
        '''
        return super().unstage()

    def stop(self, success=False):
        self.setToStoredValue()


class _SelectedSteerer(Device):
    setpoint = Cpt(SignalProxy, name='set',  value=np.nan, kind='hinted', lazy=False)
    readback = Cpt(SignalProxy, name='rdbk', value=np.nan, kind='hinted', lazy=False)

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
        cls_name = self.__class__.__name__
        txt = f'{cls_name}:{__name__}.read() returns = {r}'
        self.log.debug(txt)
        return r

    def set(self, value):
        sel = self._selected_steerer
        assert(sel is not None)
        return sel.set(value)

    def stop(self, success=False):
        sel = self._selected_steerer
        if sel is not None:
            sel.stop(success=success)

    def __del__(self):
        self.unsubscribeSelected()


class SelectedSteerer(Device):
    """Pass it through ...
    """
    dev = Cpt(_SelectedSteerer, '')

    def trigger(self):
        return self.dev.trigger()

    def stop(self, success=False):
        self.dev.stop(success=success)


class SteererCollection(Device):
    steerers = DDC(
        ad_group(Steerer, t_steerers, kind=Kind.normal, lazy=False),
        doc='all steerers', default_read_attrs=(),
    )

    steerer_names = Cpt(Signal, name='steerer_names', value=t_steerer_names, kind=Kind.config)
    selected = Cpt(Signal, name='selected', value='none selected')
    sel = Cpt(SelectedSteerer, name='sel_st')

    _default_config_attrs = ('steerer_names',)
    _default_read_attrs = ('selected', 'sel')

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
            if status is None:
                status = r
            else:
                status = AndStatus(status, r)
        return status

    def trigger(self):
        status = self.sel.trigger()
        fmt = "{}.trigger: {} "
        self.log.debug(fmt.format(self.name, status))
        return status

    def stop(self, success=False):
        self.sel.stop(success=success)
