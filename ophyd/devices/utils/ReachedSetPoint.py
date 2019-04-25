from ophyd import PVPositionerPC
from ophyd.utils import errors
from ophyd.status import SubscriptionStatus, Status

class OphydInvalidParameter(ValueError, errors.OpException):
    """given parameter was invalid
    """
    pass


class OphydMethodNotOverloaded(AssertionError, errors.OpException):
    """
    """
    pass

#t_super = Device

#: It has to be PVPositionerPC so that it will work
t_super = PVPositionerPC
class DoneBasedOnReadback(t_super):
    """Wait until readback is matching setpoint within requested precision

    The idea of this class is to mimic a proper done variable using
    setpoint and readback value. Then the done variable should be
    set when the readback value matches the setpoint value within
    the specified precision.


    See :class:`ReachedSetpoint` for an implemementation of this class

    The work is done in
    This checking behaviour is implemented in
    :meth:`_positionReached`.



    The device has to provide two signal like variables:
        * setpoint
        * readback

    Warning:
        Code not yet checked

    """
    def __init__(self, *args, **kws):
        """

        Args:
            setting_parameters :
        """
        self._setting_parameters = None
        setting_parameters = kws.pop("setting_parameters", None)

        super().__init__(*args, **kws)

        setpar = self._checkSettingParameters(setting_parameters)
        if setpar is None:
            fmt = "%s._checkSettingParameters must return vaild parameters (returned None)"
            txt = fmt % (self.__class__.__name__,)
            raise AssertionError(txt)

        self._setting_parameters = setpar
        self._checkSetup()

        # Required to trace the status of the device
        self._moving = None
        self.__logger = None

    def _checkSetup(self):
        """check that instance contains required variables
        """
        assert(self.readback is not None)
        self.readback.value

        assert(self.setpoint is not None)
        self.setpoint.value
        self.setpoint.set

    def _checkSettingParameters(self, setting_parameters):
        """Check and store setting Parameters

        Overload this function to check setting parameters

        Returns:
                valid setting parameters
        """
        raise OphydMethodNotOverloaded("Overload this method")
        return setting_parameters


    def _positionReached(self, *args, **kws):
        """check that the position has been reached

        Returns: flag(bool)

        Returns true if position was reached, false otherwise
        """
        raise OphydMethodNotOverloaded("Overload this method")

    def setLogger(self, logger):
        self.__logger = logger

    @property
    def logger(self):
        return self.__logger

    def set(self, value):
        """

        Returns:
            :class:`ophyd.status.SubscriptionStatus`

        """
        def callback(*args,**kws):

            pos_valid = self._positionReached(*args, **kws)

            tup = self.__class__.__name__, args, kws, self._moving, pos_valid
            txt = "%s:set cb: args %s  kws %s: self._moving %s pos_valid %s" % tup
            #print(txt)

            logger = self.__logger
            if logger is not None:
                logger.debug(txt)

            if self._moving and pos_valid:
                self._moving = False
                return True
            else:
                self._moving = True
            return False

        pos_valid = self._positionReached(check_set_value = value)

        logger = self.logger

        if pos_valid:
            status = Status()
            status.done = 1
            status.success = 1
            tup = self.__class__.__name__, value,
            txt = "%s: no motion required for value %s" % tup
            if logger:
                logger.info(txt)
            return status


        status = SubscriptionStatus(self.readback, callback)
        self.setpoint.set(value)

        tup = self.__class__.__name__, value, status
        txt = "%s:set cb: value %s status = %s" % tup
        #print(txt)
        if logger: logger.debug(txt)

        return status

class ReachedSetpoint(DoneBasedOnReadback):
    """Setpoint within some absolute precision

    Warning:
        Its currently not unterstood if a value can be set and
        read back if the change is smaller than the value the
        IOC considers significant
    """
    def _positionReached(self, *args, **kws):
        """position within given range?
        """

        limit = self._setting_parameters

        rbk = self.readback.value

        check_set_value = kws.pop("check_set_value", None)
        if check_set_value is None:
            setp = self.setpoint.value
        else:
            setp = check_set_value


        diff = abs(rbk - setp)

        flag = diff < limit

        tup = self.__class__.__name__, setp, rbk, diff, limit, flag
        txt = "%s:_positionReached: set %s rbk %s diff %s limit %s position valid %s" % tup
        # print(txt)

        logger = self.logger
        if logger is not None:
            logger.info(txt)

        return flag

    def _checkSettingParameters(self, setting_parameters):
        """Absolute value for setting parameter

        And thus just a float
        """
        try:
            t_range = float(setting_parameters)
            assert(t_range >0)
        except ValueError as des:
            msg = "Expected a single float as setting parameter but got %s: error %s"
            raise OphydInvalidParameter(msg %(setting_parameters, des.mesg))

        return t_range
