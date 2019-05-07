"""

Warning:
    Started to test the code

"""

from ophyd import Device, EpicsSignal, EpicsSignalRO, PVPositionerPC, Component as Cpt
from ophyd.status import Status, AndStatus, DeviceStatus
from ophyd.areadetector.base import ad_group
from ophyd.device import  DynamicDeviceComponent as DDC
from ..utils import measurement_state_machine, signal_with_validation
from .quad_list import quadrupoles

#: Construct a list of quadrupoles multiplexer
t_quadrupoles = [(name, 'PMUXZR:' + name) for name in quadrupoles]

import logging
logger = logging.getLogger()



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
    readback = Cpt(EpicsSignalStr, 'QSPAZR:rdbk')
    setpoint = Cpt(EpicsSignal, 'QSPAZR:set')
    switch   = Cpt(EpicsSignal, 'QSPAZR:cmd1')
    status   = Cpt(EpicsSignalRO, 'QSPAZR:stat1')
    no_error = Cpt(EpicsSignalRO, 'QSPAZR:stat2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = logger

    def setLogger(self, logger):
        self.__logger = logger

    def set(self, value):
        fmt = "Setting power mux power converter to value {}"
        self.__logger.info(fmt.format(value))
        stat = NullStatus()
        return stat

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
    readback = Cpt(EpicsSignalStr, 'PMUXZR:name')

    #: switch power converter off ?
    off  = Cpt(EpicsSignal,   'PMUXZR:off', name = 'off')

    #: are the relays enabled?
    relay = Cpt(EpicsSignalRO, 'PMUXZR:disable')

    #: Todo: check if it is still working!
    relay_ps = Cpt(EpicsSignalRO, 'PMUXZR:relay_ps')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mux_switch_validate = signal_with_validation.FlickerSignal(self.readback, timeout=5, validation_time=3)
        self.__logger = logger

    def setLogger(self, logger):
        self.__logger = logger

    def checkPowerconverterMembers(self):
        # The multiplexer power converter
        pc = self.parent.power_converter
        pc.setpoint
        pc.setpoint.get
        pc.readback.get


    def switchMuxAndCheck(self, name, device_status):

        assert(device_status is not None)
        if name == "Off":
            # What has to be written to the device....
            rbk = self.readback.get()
            self.__logger.info('power converter command to off: rbk "{}"'.format(rbk))
            if rbk == "Mux OFF":
                # Already off nothing to do
                self.__logger.info('power converter already off: nothing to do "{}"'.format(rbk))
                device_status._finished(success = True)
                return

            status_set = self.off.set(1)

        else:
            pcs = self.parent.activate.pcs
            pc_ac = getattr(pcs, name)
            self.__logger.info("power converter activate {}".format(pc_ac))
            status_set = pc_ac.set(1)

        def cb():
            nonlocal device_status
            self.__logger.info('Switching: checking readback. Name {}'.format(name))
            self.mux_switch_validate.execute_validation(device_status, run = False)

        status_set.add_callback(cb)
        fmt = "set status {} check status {}"
        self.__logger.info(fmt.format(status_set, device_status))

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

        stat_on  = DeviceStatus(device=self.readback, timeout = self.timeout, settle_time = self.settle_time)
        def switch_on():
            """Require to chain the call backs

            To be called after switch off has been made
            """
            nonlocal name, stat_on
            self.__logger.info("Calling switch on for {}".format(name))
            self.switchMuxAndCheck(name, stat_on)

        self.switchMuxAndCheck(name, stat_on)
        return stat_on

    def set(self, value):
        """Select the power converter selector

        Todo:
           Check that the value ios correct at the end
        """

        self.checkPowerconverterMembers()
        self.mux_switch_validate.tic()
        # Check if the power converter is already selected ...
        selected = self.readback.get()
        if selected == value:
            self.__logger.info("Not switching muxer already at {}".format(value))
            status = Status(success = True, done = True)
            return status

        self.__logger.info("Switching muxer from {} to {}".format(selected, value))
        return self.switchPowerconverter(value)

        # stat = Status(success = True, done = True)
        # return stat


    def trigger(self):
        stat_rbk = self.readback.trigger()
        stat_relay = self.relay.trigger()
        stat_off = self.off.trigger()

        return AndStatus(AndStatus(stat_rbk, stat_relay), stat_off)

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
