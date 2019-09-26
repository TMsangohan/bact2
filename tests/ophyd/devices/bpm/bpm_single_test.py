from bact2.ophyd.devices.pp.bpm.bpm_single import BPMSingle, BPMCollection
import unittest
import sys

class TestOphydDevice(unittest.TestCase):
    '''Check standard properties of a device
    '''
    def setUp(self):
        self._dev = None
        self.setUpDevice()

    def tearDown(self):
        if self._dev is not None:
            # self._dev.destroy()
            del self._dev
            self._dev = None
            
    def checkConnection(self):
        if not self._dev.connected:
            self._dev.wait_for_connection()

    def test000_Names(self):
        '''Test the attribute names
        '''
        return self._dev.component_names

    def test001_DeviceReadAttributes(self):
        '''Check read attributes
        '''
        return self._dev.read_attrs
    
    def test002_DeviceConfigurationAttributes(self):
        '''Check configuratio attributes
        '''
        return self._dev.configuration_attrs

    def test003_DeviceReadConfiguration(self):
        '''Check read configuration
        '''
        return self._dev.read_configuration()

    def test004_DeviceDescribeConfiguration(self):
        '''Check read configuration
        '''
        return self._dev.describe_configuration()
        
    def test005_DeviceConnect(self):
        '''Test if a connection to the device can be established
        '''
        self.checkConnection()
    
    def test006_DeviceDescribe(self):
        '''Test the method describe
        '''
        self.checkConnection()
        return self._dev.describe()
    
    def test007_DeviceRead(self):
        '''Test if the device can be read
        '''
        self.checkConnection()
        return self._dev.read()

    def test008_DeviceSummary(self):
        '''Test if the device provides a summary

        The method :meth:`_summary` is used as as the method
        :meth:`summary` is shallow wrapper which just prints
        the return value of summary
        '''
        self.checkConnection()
        return self._dev._summary()

    def test009_DeviceInstantiatedSignals(self):
        '''Check if instantiated signals are returned
        '''
        self.checkConnection()
        g = self._dev.get_instantiated_signals()
        self.assertTrue(callable(g.__iter__))
    
    def test010_DeviceEventTypes(self):
        '''enent type attribute
        '''
        self._dev.event_types

    def test010_DeviceTuple(self):
        '''device tuple
        '''
        self._dev.get_device_tuple
        
class TestBPM0Single( TestOphydDevice ):
    '''Test of BPM as a single device
    '''
    def setUpDevice(self, bpm_name = 'BPMZ8T2R'):
        self._dev = BPMSingle(bpm_name, name = bpm_name)

    def test001_DeviceReadAttributes(self):
        r = super().test001_DeviceReadAttributes()
        print(r)
        
class TestBPM1Collection( TestOphydDevice ):
    def setUpDevice(self):
        self._dev = BPMCollection(name = 'col')
    
    def test100_BPMAccess(self):
        '''Test the collection instantiation by at least a single device
        '''
        self._dev.col.bpmz8t2r
        
        

# del TestBPM0Single
# del TestBPM1Collection


del TestOphydDevice

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
