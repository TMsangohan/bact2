from ophyd import Component as Cpt, Device, EpicsSignalRO

class BBQRFeedback( Device ):
    rms = Cpt(EpicsSignalRO,    "BBQR:X:SRAM:MAXRMSVAL")
