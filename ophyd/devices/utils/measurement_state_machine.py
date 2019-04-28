import super_state_machine
import enum

class AcquisitionState(super_state_machine.machines.StateMachine):
    """Measurement states of a flyable
    """
    class States(enum.Enum):
        """
        """
        #: e.g. at start up or if everything has been made
        IDLE = 'idle'
        #: after the devices was called with kickoff
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
            'idle': ['acquire', 'failed'],
            #: 
            'acquire' : ['validate', 'failed'],
            #: only start acquiring data if in idle state
            'validate' : ['finished', 'failed'],
            #: finished state only if in acquiring
            'finished' : ['idle', 'failed'],
            #: failed can be always made to
            #: Todo:
            #:   check for wildcard option
            'failed' : ['idle', 'failed']
         }