import bluesky.plans as bp
from bluesky.utils import ProgressBarManager
from bluesky.callbacks import LivePlot
from bluesky import RunEngine
import bluesky.callbacks as bc
import bluesky.callbacks.best_effort
from cycler import cycler
from functools import partial
import databroker
import pickle

# If jupyter is used it would be :func:`bluesky.utils.install_nb_kicker`
# The call to the :class:`bluesky.RunEngine` has then to be made on the
# notebook command line
from bluesky.utils import install_qt_kicker

# In the office experimentation with master clock is not the best to have
from ophyd import Component as Cpt, Device, EpicsSignalRO, EpicsSignal, sim, PVPositionerPC
from ophyd.status import DeviceStatus, SubscriptionStatus, Status

# Used to generate a dedicated frequency plan
import copy
import numpy as np
import io
import time
import threading


class PPREWaveformgeneratorFrequency( PVPositionerPC ):
    setpoint = Cpt(EpicsSignal,   ":setFrq")
    readback = Cpt(EpicsSignalRO, ":rdFrq")

class PPREWaveformgenerator( Device ):
    freq = Cpt(PPREWaveformgeneratorFrequency, 'WFGENC1S10G', egu='Hz', settle_time = 1.0,
            timeout = 1.0,
               #setting_parameters = .1
    )

    

class BBQRFeedback( Device ):
    rms = Cpt(EpicsSignalRO,    "BBQR:X:SRAM:MAXRMSVAL")


def re():
    bec = bc.best_effort.BestEffortCallback()
    RE = RunEngine({})
    RE.log.setLevel("INFO")
    RE.subscribe(bec)
    install_qt_kicker()
    RE.waiting_hook = ProgressBarManager()
    db = databroker.Broker.named('temp')
    RE.subscribe(db.insert)

    return RE

def run():

    f0 = 1030e3
    f1 = 1030.5e3
    freq = np.linspace(f0, f1, 6)
    #f1 = 1080e3
    #freq = np.linspace(f0, f1, 500)
    wf = PPREWaveformgenerator(name = "waveform")
    if not wf.connected:
        wf.wait_for_connection()

    
    sw_freq = cycler(wf.freq, freq)

    fb = BBQRFeedback(name = "ppre_fb")
    det = [fb]


    cmd = partial(bp.scan_nd, det, sw_freq)
    return cmd

    uids = RE(
    )
    print(uids)
    headers = db[uids]

    header = headers[0]
    print(header)
    print(header.stream_names)
    df = header.table()
    df.to_csv("ppre_scan.csv")
    print(header.table())
    print(header.fields())

if __name__ == '__main__':
    #test()
    run()

