#Let's test that the epics variables are really available
import matplotlib
matplotlib.use('Qt4agg')
import matplotlib.pyplot as plt
import time

# import epics
# import functools

# Select a read only variable which gives a new output every now and then
# I could use the simulation ones from ophyd. I prefer to use some real 
# device

# One read only device
sig_ro = 'TOPUPCC:rdCur'

# A second read only device
sig_ro2 = 'MCLKHX251C:freq'






from bluesky import plans as bp, RunEngine
from bluesky.utils import install_qt_kicker, ProgressBarManager
from ophyd import Device, Component as Cpt, EpicsSignalRO
from bluesky.callbacks.best_effort import BestEffortCallback

class LogMethodCalls:
    def trigger(self):
        status = super().trigger()
        cls_name = self.__class__.__name__
        self.log.debug(f'{cls_name} method trigger returned {status}')
        return status
    
    def read(self):
        result = super().read()
        cls_name = self.__class__.__name__
        self.log.debug(f'{cls_name} read returned {result}')
        return result

#_oDevice = ophyd.Device
#class Device(LogMethodCalls, _oDevice):
#    pass

#_oEpicsSignalRO = ophyd.EpicsSignalRO
#class EpicsSignalRO(LogMethodCalls, _oEpicsSignalRO):
#    pass



class ReadonlyDevice(Device):
    """A simple sample device
    
    This devivce is solely used to describe the methods
    """
    ro = Cpt(EpicsSignalRO, sig_ro)

# Check that debug print works!
# logging.basicConfig(level = 'INFO')
# RE.log.setLevel('DEBUG')
# ophyd.logger.setLevel('DEBUG')

def main():
    ro_dev = ReadonlyDevice(name = 'sig')
    #ro_dev.log.addHandler(stream_handler)
    # ro_dev.log.setLevel('DEBUG')

    if not ro_dev.connected:
        ro_dev.wait_for_connection()

    RE = RunEngine({})
    bec = BestEffortCallback()
    RE.subscribe(bec)
    RE.waiting_hook = ProgressBarManager()
    install_qt_kicker()

    print(ro_dev.read())

    detectors = [ro_dev]
    RE(bp.count(detectors, 1))

    del RE
    del ro_dev
    print("Finished")

if __name__ == '__main__':
    main()
