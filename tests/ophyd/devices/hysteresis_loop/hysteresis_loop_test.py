from bact2.ophyd.devices.pp.hysteresis_loop import TracingHysteresisModel
import unittest
import sys

class TracingHysteresisModelTestDev(TracingHysteresisModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_value = None

    def getCurrentValue(self):
        assert(self._current_value is not None)
        return self._current_value

    def set(self, value):
        super().set(value)
        self._current_value = current_value

class TestTHM(unittest.TestCase):
    '''
    '''
    def setUp(self):
        self.tracing_model = s TracingHysteresisModelTestDev(lower_limit = 0, upper_limit = 1)
        self.set(0)

    def test000(self):
        '''Test if the model exists at all
        '''

def main():
    '''

    Todo:
        Ophyd does not necessarily use epics.PV / epics.ca

    Warning:
        These tests frequently crash the system
    '''
    #import epics.ca

    try:
        #epics.ca.initialize_libca()
        #epics.ca.use_initial_context()

        unittest.main()

    finally:
        #epics.ca.finalize_libca()
    
if __name__ == '__main__':
    main()
