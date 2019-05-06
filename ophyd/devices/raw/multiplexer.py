"""

Warning:
    Untested code!

"""
from ophyd import Device, EpicsSignal, EpicsSignalRO, PVPositionerPC, Component as Cpt
from ophyd.status import Status

class MultiplexerPowerConverter( PVPositionerPC ):
    """Access to the multiplexer value
    """
    readback = Cpt(EpicsSignal,   'QSPAZR:rdbk')
    setpoint = Cpt(EpicsSignal,   'QSPAZR:set')


class MultiplexerSelector( PVPositionerPC ):
    """Select the power converter to speak to

    Warning:
        Untested code

    This code must ensure that the power converter is off before
    switching to an other power converter.
    """

    #: switch power converter off ?
    off  = Cpt(EpicsSignal,   'PMUXZR:off')

    #: set the power converter to the new value
    setpoint = Cpt(EpicsSignal, 'PMUXZR:name')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def check_powerconverter_members(self):
        # The multiplexer power converter
        pc = self.parent.power_converter
        pc.setpoint
        pc.setpoint.get
        pc.readback.get

    def switch_powerconverter(value):

        self.check_powerconverter_members()
        pc = self.parent.power_converter

        # Make sure the power converter is off
        check_value = pc.setpoint.get()
        assert(check_value == 0)

        check_value = pc.readback.get()
        assert(check_value == 0)

        # What has to be written to the device....
        self.off.set("")

        # If that's all made set the power convert
        # self.setpoint.set(value)

        # And switch it back on again

        status = Status()
        status.done = True
        status.success = True
        return status

    def set(self, value):
        """Select the power converter to multiplex to
        """
        self.check_powerconverter_members()

        # Check if the power converter is already selected ...
        selected = self.setpoint.get()
        if selected == value:
            status = Status()
            status.done = True
            status.success = True
            return status

        return self.switch_powerconverter()


class Multiplexer( Device ):
    selector = Cpt(MultiplexerSelector,
                    settle_time = 5.0, timeout = 10.0)

    power_converter = Cpt(MultiplexerPowerConverter, name = "mux_pc", egu = "A")
