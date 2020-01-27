"""

Warning:
    Started to test the code

"""

from ophyd import Device, Signal, EpicsSignal, EpicsSignalRO, PVPositionerPC, Component as Cpt
from ophyd.status import Status, AndStatus, DeviceStatus
from ophyd.areadetector.base import ad_group
from ophyd.device import  DynamicDeviceComponent as DDC
from ..utils import measurement_state_machine, signal_with_validation
from .quad_list import quadrupoles

#: Construct a list of quadrupoles multiplexer
t_quadrupoles = [(name, 'PMUXZR:' + name) for name in quadrupoles]

import logging
logger = logging.getLogger()

import time


class TEpicsSignal( EpicsSignal ):
    """
    """
    def set(self, *args, **kwargs):
        r = super().set(*args, **kwargs)
        fmt = "{}.set(args = {} kwargs = {} -> {}"
        print(fmt.format(self.name, args, kwargs, r))
        return r

class EpicsSignalStr( EpicsSignalRO ):
    def read(self):
        r = super().read()
        d = {}
        for key, item in r.items():
            if key == 'value':
                item = item.replace(' ', '_')
            d[key] = item
        print("{} read to {}".format(self.name, r))
        return r

class MultiplexerPowerConverter( PVPositionerPC ):
    """Access to the multiplexer value
    """
    readback = Cpt(EpicsSignal,   'QSPAZR:rdbk')
    setpoint = Cpt(EpicsSignal,   'QSPAZR:set')
    switch   = Cpt(EpicsSignal,   'QSPAZR:cmd1')
    status   = Cpt(EpicsSignalRO, 'QSPAZR:stat1')
    no_error = Cpt(EpicsSignalRO, 'QSPAZR:stat2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setLogger(self, logger):
        self.log = logger

    def set(self, value):
        fmt = "Setting power mux power converter to value {}"
        self.log.info(fmt.format(value))
        stat = NullStatus()
        return stat

    def setToZero(self):
        '''Set current to 0.
        '''
        self.setpoint.value = 0

    def stop(self):
        self.setToZero()

    def unstage(self):
        self.setToZero()

class MultiplexerPCWrapper( Device ):
    """Create the list of power converter set PV"s
    """
    pcs = DDC(ad_group(EpicsSignal, t_quadrupoles, put_complete = True),
        doc='the multiplexer power converter selector pvs',
              default_read_attrs = (),
    )


class MultiplexerSelector( PVPositionerPC ):
    """Select the power converter to speak to

    Warning:
        Untested code

    This code must ensure that the power converter is off before
    switching to an other power converter.
    """
    #: set the power converter to the new value
    # setpoint = Cpt(TEpicsSignal, 'PMUXZR:name', )

    #: read back which power converter is selected
    readback = Cpt(EpicsSignal, 'PMUXZR:name')

    #: store the one that was explicitily set
    selected = Cpt(Signal, name='selected', value ='non stored')

    #: setpoint as index number
    setpoint_num = Cpt(Signal, name='setpoint_num', value = -1)
    #: selected as index number
    selected_num = Cpt(Signal, name='selected_num', value = -1)

    #: switch power converter off ?
    off  = Cpt(EpicsSignal,   'PMUXZR:off', name = 'off')

    #: are the relays enabled?
    relay = Cpt(EpicsSignalRO, 'PMUXZR:disable')

    #: Todo: check if it is still working!
    relay_ps = Cpt(EpicsSignalRO, 'PMUXZR:relay_ps')

    #: How long did it take to set the value
    set_time = Cpt(Signal, name = "set_time", value = -1)

    #: How long did it take to set the value
    last_wait = Cpt(Signal, name = "last_wait", value = -1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # use a long validation time let's see if there are more changes
        self.mux_switch_validate = signal_with_validation.FlickerSignal(self.readback, timeout=3, validation_time=2)
        self._timestamp = time.time()

    def setLogger(self, logger):
        self.log = logger

    def checkPowerconverterMembers(self):
        # The multiplexer power converter
        pc = self.parent.power_converter
        pc.setpoint
        pc.setpoint.get
        pc.readback.get


    def checkMuxSwitches(self, cnt_called, set_traced, selected_device_name,
                         old_value = None, value = None, **kwargs):
        """Callback to follow that mux switches happen as expected

        The muxer behaves in the following manner:

        * If it was off:
            1. response: the name of the selceted device
            2. response: Mux Off
            3. response: the name of the selected device

        * If a power converter was selected
            1. response: Mux Off
            2. response: the name of the selected device

        * And then there is one more thing:
           1. It has directly set from the last selected device
              to the requested one


        Thou shall use state machines!
        """
        assert(value is not None)


        stored =  self.selected.get()
        fmt = "cnt called {} value {} old value {} selected device {} stored {}"
        self.log.info(fmt.format(cnt_called, value, old_value, selected_device_name, stored))

        add = 0
        do_finish = False
        if cnt_called == 1:
            if old_value == "Mux OFF" and value == selected_device_name:
                fmt = 'selector was off  old_value {} == "Mux OFF" and value {} == selected device {} last set {}!'
                self.log.info(fmt.format(old_value, value, selected_device_name, stored))

            elif value == "Mux OFF" and (stored == 'not stored' or old_value == stored):
                fmt = 'value {} ==  selected device {} expecting two more steps ( old_value = {} != Mux OFF, last set {})'
                self.log.info(fmt.format(value, selected_device_name, old_value, stored))
                # Expect that we are going to reading three directly
                add = 1

            elif value == selected_device_name and old_value == stored:
                fmt = 'Expecting no more steps value {} ==  selected device {},  old_value {} == stored {})'
                self.log.info(fmt.format(value, selected_device_name, old_value, stored))
                do_finish = True
                add = 2

            else:
                txt = (
                    f'value {value} old_value {old_value}'
                    ' did not expect this set of values. '
                    'selected device {selected_device_name} last set {stored}!'
                )
                if stored == 'non stored':
                    self.log.error(txt + 'Currently ignoring this error')
                else:
                    raise AssertionError(txt)

        elif cnt_called == 2:
            if value != "Mux OFF":
                txt = (
                    f'expected value "Mux OFF" but got value "{value}"'
                    f' selected_device_name = {selected_device_name}'
                    f' old value = {old_value}'
                )
                self.log.error(txt)

                if stored != 'non stored':
                    raise AssertionError(txt)

                # We could end up here: Started muxer but still magnet selected ....
                txt2 = 'Currently accepting it as stored {stored} == "non stored"'
                self.log.error(txt2)

                add = 1
                do_finish = 1

        elif cnt_called == 3:
            do_finish = True


        else:
            fmt = "Did not expect to be called {} > 3 times value {} old value {}"
            raise AssertionError(fmt.format(cnt_called, value, old_value))

        if do_finish:
            fmt = "cnt finished called {} value {}"
            self.log.info(fmt.format(cnt_called, value))
            if value == selected_device_name:
                set_traced._finished()
            else:
                fmt = 'expected value "{} but got value "{}"'
                raise AssertionError(fmt.format(selected_device_name, value))

        return add

    def switchMuxAndTrace(self, selected_device_name, device_status):
        """switch the muxer directly from device

        Checks the changes by following the switching on and off


        Works in the following manner:
           1. a callback trace_cb is registed to readback
           2. the callback trace_cb calls :meth:`checkMuxSwitches`.
              This method checks that the muxer is switched off
              and back to the are made as expected. This method is
              expected to call :meth:`_finished` on set_traced.
           3. When this happens the validate_cb is called. This
              callback uses
              :class:`signal_with_validation.FlickerSignal`.
              This signal is used, as the muxer sends some extra
              value sometimes. FlickerSignal will set the
              device_status to finished when no further data arrives.
           4. Furthermore the readback callback is removed
           5. Finally a callback :func:`store_selected` will be called.
              This stores the name of the selected quadrupole and its
              number.

        """
        pcs = self.parent.activate.pcs
        pc_ac = getattr(pcs, selected_device_name)
        self.log.info("power converter activate {}".format(pc_ac))

        cnt_called = 0

        set_traced  = DeviceStatus(device=self.readback, timeout=self.timeout, settle_time=self.settle_time)

        def trace_cb(*args,  **kwargs):
            nonlocal cnt_called, set_traced, selected_device_name
            cnt_called +=1
            add = self.checkMuxSwitches(cnt_called, set_traced, selected_device_name, **kwargs)
            cnt_called += add

        def remove_trace_cb():
            nonlocal trace_cb
            self.readback.clear_sub(trace_cb)

        def validate_cb():
            nonlocal device_status
            self.log.info('Switching: checking readback. Name {}'.format(selected_device_name))
            self.mux_switch_validate.execute_validation(device_status, run=True)

        def store_selected():
            nonlocal selected_device_name

            val = self.readback.get()

            if val != selected_device_name:
                fmt = "Expected that device is selected {} but found device {}"
                raise AssertionError(fmt.format(selected_device_name, val))

            num = quadrupoles.index(val)
            self.log.info('Storing last set to {} as num {}'.format(val, num))
            self.selected.set(val)
            self.selected_num.set(num)

            now = time.time()
            dt = now - self._timestamp
            self.set_time.set(dt)

            self.last_wait.set(self.mux_switch_validate.stored_dt())

        set_traced.add_callback(validate_cb)
        set_traced.add_callback(remove_trace_cb)
        device_status.add_callback(store_selected)

        n_cbs = len(self.readback.subscriptions)
        fmt = "Switching readback has {} subscriptions"
        self.log.info(fmt.format(n_cbs))

        self.readback.subscribe(trace_cb, run=False)
        status_set = pc_ac.set(1)

    def switchMuxAndCheck(self, name, device_status):
        """Switch the muxer if required

        See :meth:`switchMuxAndTrace` for the heavy lifting

        Todo:
            Check if the status should not be returned ....
        """
        assert(device_status is not None)
        if name == "Off":
            # What has to be written to the device....
            rbk = self.readback.get()
            self.log.info('power converter command to off: rbk "{}"'.format(rbk))
            if rbk == "Mux OFF":
                # Already off nothing to do
                self.log.info('power converter already off: nothing to do "{}"'.format(rbk))
                device_status._finished(success = True)
                return

            status_set = self.off.set(1)

        else:
            self.switchMuxAndTrace(name, device_status)

    def switchPowerconverter(self, name):
        """select the power converter to pack on

        Now directly switching to the power converter required
        """

        # self.checkPpowerconverterMembers()
        pc = self.parent.power_converter

        # Make sure the power converter is off
        check_value = pc.setpoint.get()

        assert(check_value == 0)
        assert(self.readback is not None)

        stat_on = DeviceStatus(device=self.readback, timeout=self.timeout, settle_time=self.settle_time)
        self.switchMuxAndCheck(name, stat_on)
        return stat_on

    def set(self, value):
        """Select the power converter selector

        Todo:
           Check that the value ios correct at the end
        """

        self._timestamp = time.time()
        num = quadrupoles.index(value)
        self.setpoint_num.set(num)
        del num

        self.checkPowerconverterMembers()
        self.mux_switch_validate.tic()
        # Check if the power converter is already selected ...
        selected = self.readback.get()
        if selected == value:
            self.log.info("Not switching muxer already at {}".format(value))
            status = Status(success = True, done = True)
            return status

        self.log.info("Switching muxer from {} to {}".format(selected, value))
        return self.switchPowerconverter(value)

        # stat = Status(success = True, done = True)
        # return stat


    def trigger(self):
        stat_rbk = self.readback.trigger()
        stat_relay = self.relay.trigger()
        stat_off = self.off.trigger()

        return AndStatus(AndStatus(stat_rbk, stat_relay), stat_off)


    def switchOff(self):
        self.log.warning('Would switching multiplexer off: disabled for development')
        # Off
        # self.off.set(1)

    def stage(self):
        """

        Just for symmetry
        """

    def unstage(self):
        """

        Todo:
           To be sure that its left over as off
        """
        self.switchOff()

    def stop(self, success=False):
        self.switchOff()


class Multiplexer( Device ):
    """

    If the multiplexer is switching the power converter current must be 0!
    A deviation of 1 mA is acceptable.

    Warning:
         This code is not yet tested. Do not use it if you do not know what
         you are doing.
    """
    selector = Cpt(MultiplexerSelector, name = 'selector',
                    settle_time = 0.5, timeout = 10.0)

    power_converter = Cpt(MultiplexerPowerConverter, name = "mux_pc", egu = "A")
    activate = Cpt(MultiplexerPCWrapper, name = 'activate')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.selector.checkPowerconverterMembers()


    def unstage(self):
        self.power_converter.unstage()
        # self.selector.unstage()

    def stop(self, success=False):
        self.power_converter.stop(success=success)
        # self.selector.stop(success=success)
