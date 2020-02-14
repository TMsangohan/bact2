from ....math.utils import compare_value

from ophyd import PVPositionerPC, Component as Cpt, Signal
from ophyd.utils import errors
from ophyd.status import SubscriptionStatus, Status, AndStatus
import logging

logger = logging.getLogger()


class OphydInvalidParameter(ValueError, errors.OpException):
    """given parameter was invalid
    """
    pass


class OphydMethodNotOverloaded(AssertionError, errors.OpException):
    """
    """
    pass

# t_super = Device


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

    Todo:
        Check __init__ handling timeout
    """

    def __init__(self, *args, **kws):
        """

        Args:
            setting_parameters :
        """
        self._setting_parameters = None
        self._timeout = None
        setting_parameters = kws.pop("setting_parameters", None)

        timeout = kws.pop("timeout", 0.0)
        timeout = float(timeout)

        super().__init__(*args, **kws)

        setpar = self._checkSettingParameters(setting_parameters)
        if setpar is None:
            cls_name = self.__class__.__name__
            txt = (
                f'{cls_name}._checkSettingParameters must return'
                ' valid parameters (returned None)'
            )
            raise AssertionError(txt)

        self._setting_parameters = setpar
        self._timeout = timeout
        self._checkSetup()

        # Required to trace the status of the device
        self._moving = None

    def _checkSetup(self):
        """check that instance contains required variables
        """
        assert(self.readback is not None)
        self.readback.value

        assert(self.setpoint is not None)
        self.setpoint.value
        self.setpoint.set

        assert(self._timeout > 0)

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

    def set(self, value):
        """

        Returns:
            :class:`ophyd.status.SubscriptionStatus`

        """
        def callback(*args, **kws):

            pos_valid = self._positionReached(*args, **kws)

            cls_name = self.__class__.__name__
            txt = (
                f'{cls_name}:set cb: args {args}  kws {kws}:'
                f' self._moving {self._moving} pos_valid {pos_valid}'
                )
            self.log.debug(txt)

            if self._moving and pos_valid:
                self._moving = False
                return True
            else:
                self._moving = True
            return False

        pos_valid = self._positionReached(check_set_value=value)

        if pos_valid:
            status = Status()
            status.done = 1
            status.success = 1
            cls_name = self.__class__.__name__
            txt = f"{cls_name}: no motion required for value {value}"
            self.log.info(txt)
            return status

        self.log.info(f'settle time {self.settle_time}')
        stat_rbk = SubscriptionStatus(self.readback, callback,
                                      timeout=self._timeout,
                                      settle_time=self.settle_time)
        stat_setp = self.setpoint.set(value, timeout=self._timeout)

        status = AndStatus(stat_rbk, stat_setp)
        cls_name = self.__class__.__name__
        txt = f"{cls_name}:set cb: value {value} status = {status}"
        # print(txt)
        if logger:
            logger.debug(txt)

        return status


class ReachedSetpoint(DoneBasedOnReadback):
    """Setpoint within some absolute precision

    Obsolete class use :class:`ReachedSetpointEPS` instead
    """
    def __init__(self, *args, **kwargs):
        msg = 'Obsolete class use ReachedSetpointEPS instead'
        raise NotImplementedError(msg)


class ReachedSetpointEPS(DoneBasedOnReadback):
    """Setpoint within some absolute and relative precision
    """
    eps_rel = Cpt(Signal, name='eps_rel', value=1e-9)
    eps_abs = Cpt(Signal, name='eps_abs', value=1e-9)

    def _correctReadback(self, val):
        return val

    def _positionReached(self, *args, **kws):
        """position within given range?
        """
        rbk = self.readback.value
        rbk = self._correctReadback(rbk)

        check_set_value = kws.pop("check_set_value", None)
        if check_set_value is None:
            setp = self.setpoint.value
        else:
            setp = check_set_value

        eps_abs = self.eps_abs.value
        eps_rel = self.eps_rel.value

        t_cmp = compare_value(rbk, setp, eps_abs=eps_abs, eps_rel=eps_rel)
        flag = t_cmp == 0
        c_name = str(self.__class__)
        txt = (
            f'{c_name}:_positionReached: set {setp} rbk {rbk} '
            f'eps: abs {eps_abs} rel {eps_rel} '
            f'comparison {t_cmp} position valid {flag}'
        )
        # print(txt)

        self.log.info(txt)
        return flag

    def _checkSettingParameters(self, unused):
        """Absolute value for setting parameter

        And thus just a float
        """
        eps_abs = self.eps_abs.value
        try:
            t_range = float(eps_abs)
            assert(t_range > 0)
        except ValueError as des:
            msg = f"Expected eps_abs {eps_abs}  >0 got: error {des}"
            raise OphydInvalidParameter(msg)

        eps_rel = self.eps_rel.value
        try:
            t_range = float(eps_rel)
            assert(t_range > 0)
        except ValueError as des:
            msg = f"Expected eps_rel {eps_rel}  >0 got: error {des}"
            raise OphydInvalidParameter(msg)

        return True
