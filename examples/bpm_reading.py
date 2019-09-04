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
from bact2.ophyd.devices.pp import bpm_gains

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
    n_meas = 50

    # The frequency range
    f0 = 10
    f1 = 14
    freq = np.linspace(f0, f1, 5)


    # These are the gains
    _, gx, gy = bpm_gains.load_bpm_gains()

    bpm = BPMStorageRing(name = "bpm")
    cs = sim.motor2

    # cs.inform_set_done = bpm.waveform.new_trigger
    repeat = cycler(cs, range(n_meas))

    sw_freq = cycler(sim.motor, freq)

    # A hack on missing gains
    lgx = len(gx)
    assert(lgx == len(gy))
    if lgx > bpm.waveform.n_valid_bpms:
        raise AssertionError('got more gains than expected')
    elif lgx < bpm.waveform.n_valid_bpms:
        gx_s = np.ones((bpm.waveform.n_valid_bpms,), dtype = np.float_)
        gy_s = np.ones((bpm.waveform.n_valid_bpms,), dtype = np.float_)
        gx_s[:lgx] = gx
        gy_s[:lgx] = gy
        gx, gy = gx_s, gy_s

    bpm.waveform.x.gain.value = gx
    bpm.waveform.y.gain.value = gy


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

    # a simpler plot for the status
    fig2 = plt.figure(2)
    ax_s = plt.subplot(111)

    # let's make one large plot displaying x and y readings next to
    # the raw data readings
    fig1 = plt.figure(1, figsize=[16,12])

    ax_x = plt.subplot(221)
    ax_y = plt.subplot(222)
    ax_xr = plt.subplot(223)
    ax_yr = plt.subplot(224)
    RE(bp.scan_nd(det, sw_freq * repeat),
       [
           line_index.PlotLineVsIndexOffset("bpm_waveform_x_pos_raw", ax = ax_x, legend_keys = ['x raw']),
           line_index.PlotLineVsIndexOffset("bpm_waveform_y_pos_raw", ax = ax_y, legend_keys = ['y raw']),
           line_index.PlotLineVsIndexOffset("bpm_waveform_x_pos", ax = ax_xr, legend_keys = ['x']),
           line_index.PlotLineVsIndexOffset("bpm_waveform_y_pos", ax = ax_yr, legend_keys = ['y']),
           line_index.PlotLineVsIndex("bpm_waveform_status", ax = ax_s, legend_keys = ['stat']),
       ]
    )


if __name__ == '__main__':
    plt.ion()
    main()
    plt.ioff()
    plt.show()
