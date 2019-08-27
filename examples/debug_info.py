'''Enabling logger for logging devices

Bluesky comes with a nicely tweaked logging print. Every device has a logging
instance. This examples shows how to activate the device logging and intercept
its methods so that one can see its output

Warning:
    Currently work in progress. I do not yet fully understand how it works
'''
from bluesky import plans as bp, RunEngine
from ophyd import Device, Component as Cpt, EpicsSignalRO


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

_oDevice = Device
class Device(LogMethodCalls, _oDevice):
    pass

_oEpicsSignalRO = EpicsSignalRO
class EpicsSignalRO(LogMethodCalls, _oEpicsSignalRO):
    pass


class ReadonlyDevice(Device):
    """A simple sample device
    
    This devivce is solely used to describe the methods
    """
    ro = Cpt(EpicsSignalRO, 'TOPUPCC:rdCur')


def main():
    ro_dev = ReadonlyDevice(name = 'sig')
    
    if not ro_dev.connected:
        ro_dev.wait_for_connection()

    RE = RunEngine({})
    RE.log.setLevel('INFO')

    # Is there a simpler method for that?
    th = RE.log.parent.handlers[0]
    
    ro_dev.log.parent.setLevel('DEBUG')
    ro_dev.log.parent.addHandler(th)
    
    detectors = [ro_dev]
    RE(bp.count(detectors, 1))

if __name__ == '__main__':
    main()
