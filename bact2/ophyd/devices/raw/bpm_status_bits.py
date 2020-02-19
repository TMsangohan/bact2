'''Status bits of the BESSY II Beam position monitors
'''
import enum

class StatusBits(enum.IntEnum):
    '''BESSY II beam position monitors status bits
    '''
    automatic_gain_control = 0
    power  = 1
    # status bits below
    single_turn_mode = 2
    diag_mode = 3
    adr_a0 = 4
    adr_a1 = 5
    cs_select = 6
    live = 7
    
bpmb_its = [
    #: AGC ... Automatic gain control
    #: if not set the bpm is in saturation
    (0, "AGC", "AGC"),
    #: bpm is powered
    (1, "Pwr", "Power"),
    #: unused since 20 years
    (2, "STmode", "Single Turn Mode"),
    #: The bits further down require to be documented
    (3, "DiagMode", "Diag. Mode"),
    (4, "ADRA0", "ADR A0"),
    (5, "ADRA1", "ADR A1"),
    (6, "CS", "CS Select"),
    (7, "Live", "Live Bit"),
]
