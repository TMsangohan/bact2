from ..utils import errors

import super_state_machine.machines
import numpy as np
import logging
import enum

#: default logger
logger = logging.getLogger('bact2')

from ....math.utils import compare_value

class HystereisFollowState(super_state_machine.machines.StateMachine):
    """States when following a hysteresis loop
    """
    class States(enum.Enum):
        """
        """
        #: e.g. at start up
        UNKNWON = 'unknown'
        #: Ramping up
        RAMP_UP = 'ramp_up'
        #: Ramping down
        RAMP_DOWN = 'ramp_down'
        # Special treatment of the edges
        #: top end
        TOP = 'top'
        #: bootom end
        BOTTOM = 'bottom'
        #: Follow failed
        FAILED = 'failed'

    class Meta:
        initial_state = "unknown"
        transitions = {
            #: start to ramp up or down to get to
            #: leave unknwon state
            'unknown'  : ['ramp_up', 'ramp_down', 'top', 'bottom', 'failed'],
            #: not tracking if sufficient number of cycles made
            'ramp_up'  : ['top',       'failed'],
            #:
            'ramp_down': ['bottom',    'failed'],
            'top'      : ['ramp_down', 'failed'],
            'bottom'   : ['ramp_up',   'failed'],
            #:
            'failed'   : ['unknown',   'failed'],
         }


class HysteresisModel:
    '''

    Provides:
        * tracing of the hysteresis loop
    '''
    def __init__(self, *, bottom_value=None, top_value=None,
                 eps_abs=1e-6, eps_rel=1e-6, log=None):

        self.hysteresis_state = HystereisFollowState()
        self._bottom_value = bottom_value
        self._top_value = top_value

        self.eps_abs = eps_abs
        self.eps_rel = eps_rel
        if log is None:
            log = logger
        self.log = log

    def getBottomValue(self):
        assert(self._bottom_value is not None)
        return self._bottom_value

    def getTopValue(self):
        assert(self._top_value is not None)
        return self._top_value

    def getCurrentValue(self):
        '''retreive the current value the power converter is at
        '''
        raise NotImplementedError('Implement in a subclass')

    def compareValue(self, value, reference_value):
        '''Compare if the value deviates significantls from the reference value
        '''
        flag = compare_value(value, reference_value,
                             eps_abs=self.eps_abs, eps_rel=self.eps_rel)
        if flag not in (-1, 0, 1):
            raise AssertionError(f'Got invalid flag {flag}')
        return flag


    def checkRange(self, value, low_limit, high_limit):
        '''check that the value is witin a given range
        '''
        flag_low  = self.compareValue(value, low_limit)
        flag_high = self.compareValue(value, high_limit)

        if flag_low < 0:
            txt = (
                f'value {value} < lower limit {low_limit}' +
                f' thus too low: flag {flag_low}'
            )
            self.log.error(txt)
            raise errors.OutOfRangeError(txt)

        if flag_high > 0:
            txt = (
                f'value {value} > high limit {high_limit}' +
                f' thus too low: flag {flag_low}'
            )
            self.log.error(txt)
            raise errors.OutOfRangeError(txt)


    def checkConsistency(self):
        '''Check that the current value matches the value we expect to be at
        '''

        if self.hysteresis_state.is_failed:
            txt = 'Refusing to execute hysteresis cycle on failed machine'
            raise errors.DeviceError(txt)

        current_value = self.getCurrentValue()
        top_value     = self.getTopValue()
        bottom_value  = self.getBottomValue()

        self.checkRange(current_value, bottom_value, top_value)

        if self.hysteresis_state.state == 'bottom':
            flag_low = self.compareValue(current_value, bottom_value)
            if flag_low != 0:
                txt = (
                    'Expected to be at bottom, but found not to be the case:' +
                    f' current_value {current_value}' +
                    f' != bottom_value {bottom_value}: flag {flag_low}'
                )
                self.log.error(txt)
                raise errors.OutOfRangeError(txt)

        elif self.hysteresis_state.state == 'top':
            flag_high = self.compareValue(current_value, top_value)
            if flag_high != 0:
                txt = (
                    'Expected to be at bottom, but found not to be the case:' +
                    f' current_value {current_value} !=' +
                    f' top_value {top_value}: flag {flag_high}'
                )
                raise errors.OutOfRangeError(txt)

        else:
            # No check for any other state. That the value is
            # within range has been checked above by
            # self.checkRange
            pass

    def checkValue(self, value):

        bottom_value = self.getBottomValue()
        top_value = self.getTopValue()
        self.checkRange(value, bottom_value, top_value)
        self.checkConsistency()

    def toValue(self, value):
        '''returns values required to achive to get to the
        requested value respecting the hysteresis loop

        Todo:
            Who resets the state?
        '''

        self.checkValue(value)
        # Value in range and in a consistent state
        flag = self.compareValue(value, self.getCurrentValue())
        if flag == 0:
            # Nothing to do ... hit value well enough ....
            return

        # checkConsistency checked if the current value matches the
        # state. Furthermore it was checked that requested value
        # deviates from the actual value by a significant amount

        state = self.hysteresis_state.state
        if state in ('bottom', 'top'):
            # At the bottom or top just directly to the value.
            # If to be on ramp up or ramp down is a task left
            # to the user
            yield value
            return

        elif state == 'ramp_up':
            if flag < 0:
                yield self.getTopValue()
            yield value
            return

        elif state == 'ramp_down':
            if flag < 0:
                # Need only to go up
                yield self.getBottomValue()
            yield value
            return

        else:
            txt = f'Not prepared to handle state {state}'
            raise AssertionError(txt)

    def cycleToValue(self, value, n_hysteresis_cycles):

        self.checkValue(value)

        bottom_value = self.getBottomValue()
        top_value = self.getTopValue()

        cycles = range(n_hysteresis_cycles)

        state = self.hysteresis_state.state
        if state in ('bottom', 'ramp_up'):
            for c in cycles:
                yield top_value
                yield bottom_value
            yield from self.toValue(value)
            return
        elif state in ('top', 'ramp_down'):
            for c in cycles:
                yield bottom_value
                yield top_value
            yield from self.toValue(value)
            return
        else:
            txt = f'Not prepared to handle state {state}'
            raise AssertionError(txt)

        raise AssertionError('Not expected to end up here')


class TracingHysteresisModel(HysteresisModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_failed(self):
        '''

        Warning:
            This method is expected to not fail
        '''
        self.hysteresis_state.set_failed()

    def set(self, value):
        '''trace the set value

        Warning:
            This will not set any value. It only exists to trace
            the set state
        '''

        state = self.hysteresis_state.state
        if state == 'unknown':
            return

        # Not in unknown state ... trace the loop
        try:
            self.checkValue(value)
        except Exception:
            self.set_failed()
            raise

        current_value = self.getCurrentValue()
        top_value     = self.getTopValue()
        bottom_value  = self.getBottomValue()

        flag = self.compareValue(value, current_value)
        # Now just check that the request is correct
        if state in ('bottom', 'ramp_up'):
            if flag < 0:
                self.set_failed()
                txt = (
                    f'In state {state}:' +
                    f' requested value {value} < current_value {current_value}' +
                    f': flag = {flag}'
                )
                raise errors.HysteresisFollowError(txt)

        elif state in ('top', 'ramp_down'):
            if flag > 0:
                self.set_failed()
                txt = (
                    f'In state {state}:' +
                    f' requested value {value} > current_value {current_value}:'
                    f': flag = {flag}'
                )
                raise errors.HysteresisFollowError(txt)
        else:
            raise AssertionError(f'Not expected state {state}')

        # Flags match current state ... but to which state do we switch now?
        # First handle the end points
        if state == 'bottom':
            if flag == 1:
                self.hysteresis_state.set_ramp_up()
        elif state == 'top':
            if flag == -1:
                self.hysteresis_state.set_ramp_down()

        # Now let's check if one of the end points is reached ...

        flag = self.compareValue(value, bottom_value)
        if flag == 0 and state != 'bottom':
            self.hysteresis_state.set_bottom()

        flag = self.compareValue(value, top_value)
        if flag == 0 and state != 'top':
            self.hysteresis_state.set_top()

    def startTracingRamp(self, start_state, reset_failed=True):

        if start_state not in ('top', 'bottom', 'ramp_up', 'ramp_down'):
            raise AssertionError(f'start state {start_state} unknown')

        state_machine = self.hysteresis_state
        if reset_failed:
            if state_machine.is_failed:
                state_machine.set_unknown()

        method_name = f'set_{start_state}'
        method = getattr(state_machine, method_name)
        method()
