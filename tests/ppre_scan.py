import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

import bluesky.plans as bp
from bluesky.utils import ProgressBarManager
from bluesky import RunEngine
import bluesky.callbacks as bc
import bluesky.callbacks.best_effort
from cycler import cycler

import bact2
import bact2.bluesky.hacks.callbacks
from bact2.bluesky.hacks.callbacks import LivePlot
from bact2.ophyd.devices.raw.ppre_waveform_generator import PPREWaveformgenerator
from bact2.ophyd.devices.raw.bbfb import BBQRFeedback

import databroker

# If jupyter is used it would be :func:`bluesky.utils.install_nb_kicker`
# The call to the :class:`bluesky.RunEngine` has then to be made on the
# notebook command line
from bluesky.utils import install_qt_kicker


# Used to generate a dedicated frequency plan
import numpy as np
#import io
#import time
#import threading
import functools


class PPRELivePlot(LivePlot):
    """Scale plot data
    """
    #: scale factor of y data
    #: mm/ mA
    scale_dep = 1
    def update_caches(self, x, y):
        # Scale to kHz
        x = x / 1000.
        # Scale the current
        y = y * self.scale_dep
        return super().update_caches(x,y)
    
def re():
    bec = bc.best_effort.BestEffortCallback()
    RE = RunEngine({})
    RE.log.setLevel("INFO")
    RE.subscribe(bec)
    install_qt_kicker()
    RE.waiting_hook = ProgressBarManager()

    db = databroker.Broker.named('temp')
    RE.subscribe(db.insert)
    return RE, db

def execute(RE, cmd = None, ax = None):
    
    # Required as installed matplotlib does not have a 

    if cmd is None:
        cmd = create_cmd()
        
    uids = RE(cmd(),
              PPRELivePlot("ppre_fb_rms", "waveform_freq_readback", ax = ax, marker = '.')
    )
    ax.set_xlabel("f [khz]")
    ax.set_ylabel(" bunch size [mm / mA]")
    return uids
    

def analyse(db, uid):
    headers = db[uid]

    header = headers[0]
    print(header)
    print(header.stream_names)
    df = header.table()
    df.to_csv("ppre_scan.csv")
    print(header.table())
    print(header.fields())
    
def create_cmd():

    f0 = 1040e3
    # f1 = 1030.5e3
    # freq = np.linspace(f0, f1, 6)
    f1 = 1080e3
    freq = np.linspace(f0, f1, 400 + 1)
    wf = PPREWaveformgenerator(name = "waveform")
    if not wf.connected:
        wf.wait_for_connection()

    
    sw_freq = cycler(wf.freq, freq)

    fb = BBQRFeedback(name = "ppre_fb")
    det = [fb]

    cmd = functools.partial(bp.scan_nd, det, sw_freq)
    return cmd


def run():
    RE, db = re()
    uid = execute(RE)
    analyse(db, uid)
    
if __name__ == '__main__':
    #test()
    plt.ion()
    run()

