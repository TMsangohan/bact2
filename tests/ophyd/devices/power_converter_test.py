from bact2.ophyd.devices.pp.power_converter import PowerConverterRespectingHysteresis
# from bact2.ophyd.devices.utils import errors

import numpy as np
import unittest


class PowerConverterTest(unittest.TestCase):
    def setUp(self):
        cls = PowerConverterRespectingHysteresis
        self.pc = cls('HS1PD1R', name='h1pd1r')
        self.pc.top_value.value = 20
        self.pc.bottom_value.value = 0

        if not self.pc.connected:
            self.pc.wait_for_connection()


    def test000(self):
        '''Test the device setup
        '''
        self.pc.describe()
        self.pc.read()

    def test001(self):
        '''Test if check signals works if proper set up
        '''
        self.pc.follow_readback.checkSignals()
        self.pc.follow_setpoint.checkSignals()

    def test002(self):
        '''Test if check signals works if wrong setup
        '''
        tv = self.pc.top_value
        bv = self.pc.bottom_value
        tv.value, bv.value = bv.value, tv.value

        self.assertRaises(AssertionError, self.pc.follow_readback.checkSignals)
        self.assertRaises(AssertionError, self.pc.follow_setpoint.checkSignals)

    def test010(self):
        '''Test if readback is in range
        '''
        self.pc.follow_readback.checkConsistency()
        self.pc.follow_setpoint.checkConsistency()

    def test011(self):
        '''Test if follow ramp can be set
        '''

        val = self.pc.setpoint.value
        tracer = self.pc.follow_setpoint
        flag_low  = tracer.compareValue(val, tracer.getBottomValue())
        flag_high = tracer.compareValue(val, tracer.getTopValue())
        if flag_low == 0:
            state = 'bottom'
        elif flag_high == 0:
            state = 'high'
        else:
            state = 'ramp_up'

        self.pc.startTracingRamp(state)

def main():
    '''

    Todo:
        Ophyd does not necessarily use epics.PV / epics.ca

    Warning:
        These tests frequently crash the system
    '''
    import epics.ca

    try:
        epics.ca.initialize_libca()
        epics.ca.use_initial_context()

        unittest.main()
    finally:
        epics.ca.finalize_libca()

if __name__ == '__main__':
    main()
