import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt


from cycler import cycler

import bluesky.plans as bp
import bluesky.callbacks as bc
import bluesky.callbacks.best_effort
from bluesky import RunEngine
from bluesky.utils import ProgressBarManager
from bluesky.utils import install_qt_kicker

from ophyd import sim

from bact2.ophyd.devices.pp.bpm import BPMStorageRing
import bact2
import bact2.bluesky.hacks.callbacks
from bact2.bluesky.live_plot import line_index
import numpy as np


# compatability hacks to debian stable
compat = False

def main():
    # Repeat the measurement 5 times
    n_meas = 50

    # The frequency range
    f0 = 10
    f1 = 14
    freq = np.linspace(f0, f1, 5)


    bpm = BPMStorageRing(name = "bpm")
    cs = sim.motor2

    # cs.inform_set_done = bpm.waveform.new_trigger
    repeat = cycler(cs, range(n_meas))

    sw_freq = cycler(sim.motor, freq)


    if not bpm.connected:
        bpm.wait_for_connection()

    #print (bpm.trigger())
    #print (bpm.waveform.ready.read())
    det = [bpm]

    bec = bc.best_effort.BestEffortCallback()

    RE = RunEngine({})
    # RE.log.setLevel("DEBUG")
    RE.log.setLevel("INFO")
    #print(dir(bpm))
    # bpm.waveform.measurement_state.setLogger(RE.log)

    RE.subscribe(bec)
    install_qt_kicker()
    RE.waiting_hook = ProgressBarManager()

    # serializer = Serializer('localhost',9200)
    # RE.subscribe(serializer)

    fig1 = plt.figure(1)
    ax1 = plt.subplot(211)
    ax2 = plt.subplot(212)
    fig1 = plt.figure(2)
    ax3 = plt.subplot()

    if compat:
        ax1 = AxisWrapper(ax1)
        ax2 = AxisWrapper(ax2)
        ax3 = AxisWrapper(ax3)
    RE(bp.scan_nd(det, sw_freq * repeat),
       [
           line_index.PlotLineVsIndexOffset("bpm_waveform_pos_x", ax = ax1, legend_keys = ['x']),
           line_index.PlotLineVsIndexOffset("bpm_waveform_pos_y", ax = ax2, legend_keys = ['y']),
           line_index.PlotLineVsIndex("bpm_waveform_status", ax = ax3, legend_keys = ['stat']),
       ]
    )


if __name__ == '__main__':
    plt.ion()
    main()
    plt.ioff()
    plt.show()
