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
    '''

    Todo:
       Fix gain treatment
    '''
    # Repeat the measurement 5 times
    n_meas = 1

    # The frequency range
    f0 = 10
    f1 = 14
    freq = np.linspace(f0, f1, 5)



    bpm = BPMStorageRing(name = "bpm")
    # bpm.waveform.x.gain.value = 1
    # bpm.waveform.y.gain.value = 1

    bpm_c = BPMStorageRing(name = "bpm_c")
    del bpm_c.waveform.packed_data
    bpm_c_waveform.packed_data = bpm._waveform.packed_data
    bpm_c.waveform.x.gain.value = 1
    bpm_c.waveform.y.gain.value = 1
    cs = sim.motor2

    # cs.inform_set_done = bpm.waveform.new_trigger
    repeat = cycler(cs, range(n_meas))

    sw_freq = cycler(sim.motor, freq)

    if not bpm.connected:
        bpm.wait_for_connection()



    #print (bpm.trigger())
    #print (bpm.waveform.ready.read())
    det = [bpm, bpm_c]

    bec = bc.best_effort.BestEffortCallback()

    RE = RunEngine({})
    #RE.log.setLevel("DEBUG")
    #RE.log.setLevel("INFO")
    #print(dir(bpm))
    # bpm.waveform.measurement_state.setLogger(RE.log)

    RE.subscribe(bec)
    install_qt_kicker()
    RE.waiting_hook = ProgressBarManager()

    # serializer = Serializer('localhost',9200)
    # RE.subscribe(serializer)

    # a simpler plot for the status
    fig2 = plt.figure(2)
    ax_s = plt.subplot(111)

    # let's make one large plot displaying x and y readings next to
    # the raw data readings
    fig1 = plt.figure(1, figsize=[16,12])

    ax_x  = plt.subplot(221)
    ax_y  = plt.subplot(222)
    ax_xr = plt.subplot(223)
    ax_yr = plt.subplot(224)
    RE(bp.scan_nd(det, sw_freq * repeat),
       [
           line_index.PlotLine("bpm_waveform_x_pos", "bpm_waveform_ds", ax = ax_x, legend_keys = ['x']),
           line_index.PlotLine("bpm_waveform_y_pos", "bpm_waveform_ds", ax = ax_y, legend_keys = ['y']),
           line_index.PlotLine("bpm_c_waveform_x_pos", "bpm_c_waveform_ds", ax = ax_x, legend_keys = ['x c'], marker = '.'),
           line_index.PlotLine("bpm_c_waveform_y_pos", "bpm_c_waveform_ds", ax = ax_y, legend_keys = ['y c'], marker = '.'),
           line_index.PlotLineVsIndex("bpm_waveform_x_pos_raw", ax = ax_xr, legend_keys = ['x raw']),
           line_index.PlotLineVsIndex("bpm_waveform_y_pos_raw", ax = ax_yr, legend_keys = ['y raw']),
           line_index.PlotLineVsIndex("bpm_waveform_status", ax = ax_s, legend_keys = ['stat']),
       ]
    )


if __name__ == '__main__':
    plt.ion()
    n_rep = 1
    for i in range(n_rep):
        main()
    plt.ioff()
    plt.show()
