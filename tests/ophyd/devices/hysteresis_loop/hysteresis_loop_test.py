from bact2.ophyd.devices.pp.hysteresis_loop import TracingHysteresisModel
from bact2.ophyd.devices.utils import errors

import super_state_machine.errors
import unittest


class TracingHysteresisModelTestDev(TracingHysteresisModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_value = None

    def getCurrentValue(self):
        assert(self._current_value is not None)
        return self._current_value

    def set(self, value):
        super().set(value)
        self._current_value = value


class TestTHM(unittest.TestCase):
    '''
    '''
    def setUp(self):
        self.bottom_value = 2
        self.top_value = 3
        self.val_lo  = 0.9 * self.bottom_value + 0.1 * self.top_value
        self.val_hi  = 0.1 * self.bottom_value + 0.9 * self.top_value
        self.val_mid = 0.5 * self.bottom_value + 0.5 * self.top_value
        mod = TracingHysteresisModelTestDev(top_value=self.top_value,
                                            bottom_value=self.bottom_value)
        self.tracing_model = mod

    def test000(self):
        '''Test if the model exists at all
        '''
        self.tracing_model.set(self.bottom_value)

    def test001_init_model(self):
        '''Test if the model exists at all
        '''
        self.tracing_model.set(self.bottom_value)
        self.tracing_model.hysteresis_state.set_bottom()

    def test002_medium_level(self):
        '''Test if it can be set to medium level
        '''
        self.test001_init_model()
        self.tracing_model.set(self.val_mid)
        self.assertEqual(self.tracing_model.hysteresis_state.state, 'ramp_up')

    def test003(self):
        '''From medium level to top level
        '''
        self.test002_medium_level()
        self.tracing_model.set(self.top_value)
        self.assertEqual(self.tracing_model.hysteresis_state.state, 'top')

    def test004_directly_to_top(self):
        '''Directly to top value?
        '''
        self.test001_init_model()
        self.tracing_model.set(self.top_value)
        self.assertEqual(self.tracing_model.hysteresis_state.state, 'top')

    def test005(self):
        '''From medium level to down reports failure
        '''
        self.test002_medium_level()
        self.assertRaises(errors.HysteresisFollowError,
                          self.tracing_model.set, self.bottom_value)
        self.assertTrue(self.tracing_model.hysteresis_state.is_failed)

    def test006_to_ramp_down(self):
        '''From top to medium level
        '''
        self.test004_directly_to_top()
        self.tracing_model.set(self.val_mid)
        self.assertEqual(self.tracing_model.hysteresis_state.state,
                         'ramp_down')

    def test007(self):
        '''From medium level to bottom
        '''
        self.test006_to_ramp_down()
        self.tracing_model.set(self.bottom_value)
        self.assertEqual(self.tracing_model.hysteresis_state.state, 'bottom')

    def test008(self):
        '''From top to bottom
        '''
        self.test004_directly_to_top()
        self.tracing_model.set(self.bottom_value)
        self.assertEqual(self.tracing_model.hysteresis_state.state, 'bottom')

    def test010(self):
        '''From bottom to top using hysteresis loop values
        '''
        self.test001_init_model()
        for val in self.tracing_model.toValue(self.top_value):
            self.tracing_model.set(val)

    def test011_machine_to_failed(self):
        '''Check that failed machine in signaled
        '''
        self.test001_init_model()

        self.tracing_model.set(self.val_hi)
        self.assertRaises(errors.HysteresisFollowError,
                          self.tracing_model.set, self.val_lo)
        self.assertRaises(errors.DeviceError,
                          self.tracing_model.set, self.val_hi)

    def test012(self):
        '''Follow ramp from high value to low value
        '''

        self.test001_init_model()

        self.tracing_model.set(self.val_hi)
        for val in self.tracing_model.toValue(self.val_lo):
            self.tracing_model.set(val)

        self.assertTrue(self.tracing_model.hysteresis_state.is_ramp_down)

    def test013(self):
        '''Test that ramp up can not be set on failed machine
        '''

        self.test011_machine_to_failed()
        self.assertRaises(super_state_machine.errors.TransitionError,
                          self.tracing_model.hysteresis_state.set_ramp_up)

    def test014(self):
        '''Test if a failed machine can be restarted
        '''
        self.test011_machine_to_failed()
        self.tracing_model.hysteresis_state.set_unknown()
        self.tracing_model.hysteresis_state.set_ramp_up()

        for val in self.tracing_model.toValue(self.val_lo):
            self.tracing_model.set(val)

        self.assertTrue(self.tracing_model.hysteresis_state.is_ramp_down)


if __name__ == '__main__':
    unittest.main()
