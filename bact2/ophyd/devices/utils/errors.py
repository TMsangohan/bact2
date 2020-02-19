class Bact2RuntimeError(RuntimeError):
    """Just to have the possiblity to distinquish
    """
    pass

class DeviceError(Exception):
    '''Error signaled by an device
    '''

class OutOfRangeError(DeviceError):
    '''The request gave an out of range error

    Todo:
        Check if it should not be derived from an otehr base class
    '''
    pass

class HysteresisFollowError(OutOfRangeError):
    '''
    '''