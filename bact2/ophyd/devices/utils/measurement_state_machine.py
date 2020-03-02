import super_state_machine.machines
import enum

class AcquisitionState(super_state_machine.machines.StateMachine):
    """Measurement states of a flyable
    """
    class States(enum.Enum):
        """
        """
        #: e.g. at start up or if everything has been made
        IDLE = 'idle'
        #: Trigger was received ... waiting that the device gets ready
        TRIGGERED = 'triggered'
        #: after the devices was triggered and is ready to take data
        ACQUIRE = 'acquire'
        #: acquiring data done lets go again
        VALIDATE = 'validate'
        #: finished done no more date expected
        FINISHED = 'finished'
        #: Failed: something not as expected
        FAILED = 'failed'

    class Meta:
        initial_state = "idle"
        transitions = {
            #: idle can be only set if it has finished or in
            #: sending state.
            'idle': ['triggered', 'failed'],
            #: triggered waiting to get ready
            'triggered' :  ['acquire', 'failed'],
            #: taking data
            'acquire' : ['validate', 'finished', 'failed'],
            #: only start acquiring data if in idle state
            'validate' : ['finished', 'failed'],
            #: finished state only if in acquiring
            'finished' : ['idle', 'failed'],
            #: failed can be always made to
            #: Todo:
            #:   check for wildcard option
            'failed' : ['idle', 'triggered', 'failed']
         }
