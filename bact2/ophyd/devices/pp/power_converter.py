from ..raw import power_converter
from .hysteresis_loop import TracingHysteresisModel

from ophyd import Component as Cpt, Signal, Device
import numpy as np


class PowerConverterTracingHysteresisModel( TracingHysteresisModel ):
    def __init__(self, *args, parent=None, value_name=None, **kwargs):
        assert(parent is not None)
        assert(value_name is not None)

        super().__init__(*args, **kwargs)

        # self.parent = parent
        self.value_signal = getattr(parent, value_name)
        self.top_value_signal = getattr(parent, 'top_value')
        self.bottom_value_signal = getattr(parent, 'bottom_value')

        # At this stage the call will fail
        # self.checkSignals()

    def getCurrentValue(self):
        return self.value_signal.value

    def getBottomValue(self):
        return self.bottom_value_signal.value

    def getTopValue(self):
        return self.top_value_signal.value

    def checkSignals(self):

        bottom_val = self.getBottomValue()
        assert(np.isfinite(bottom_val))

        top_val = self.getTopValue()
        assert(np.isfinite(top_val))

        val = self.getCurrentValue()
        assert(np.isfinite(val))

        flag = self.compareValue(bottom_val, top_val)
        if flag != -1:
            txt = (
                f'Expected bottom value {bottom_val} < top value {top_val}:'
                f' flag {flag} != -1'
            )
            raise AssertionError(txt)

class PowerConverterRespectingHysteresis( power_converter.PowerConverter ):
    top_value    = Cpt(Signal, name='top_value',    value=np.nan)
    bottom_value = Cpt(Signal, name='bottom_value', value=np.nan)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cls = PowerConverterTracingHysteresisModel
        self.follow_setpoint = cls(parent=self, value_name='setpoint')
        self.follow_readback = cls(parent=self, value_name='readback', eps_abs=1e-3)

        def check_setpoint_change(*args, value=None, **kwargs):
            self.follow_setpoint.set(value)
            pass

        # currently not prepared to check is
        # self.setpoint.add_callback(check_setpoint_change)

    def set(self, value):
        self.follow_setpoint.set(value)
        self.follow_readback.set(value)

        status = super().set(value)

        def check_if_failed():
            nonlocal status

            if not status.success:
                self.follow_setpoint.to_failed()
                self.follow_readback.to_failed()

        if status.done:
            check_if_failed()

        return status

    def startTracingRamp(self, start_state, reset_failed=True):

        for tracer in (self.follow_readback, self.follow_setpoint):
            tracer.checkSignals()
            tracer.startTracingRamp(start_state, reset_failed=reset_failed)
