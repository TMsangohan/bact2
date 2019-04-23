class PPREWaveformgeneratorFrequency( PVPositionerPC ):
    setpoint = Cpt(EpicsSignal,   ":setFrq")
    readback = Cpt(EpicsSignalRO, ":rdFrq")

class PPREWaveformgenerator( Device ):
    freq = Cpt(PPREWaveformgeneratorFrequency, 'WFGENC1S10G', egu='Hz', settle_time = 1.0,
            timeout = 1.0,
               #setting_parameters = .1
    )
