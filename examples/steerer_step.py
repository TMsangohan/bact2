import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

import bluesky.plans as bp
from bluesky.utils import ProgressBarManager
from bluesky.utils import install_qt_kicker

from bluesky import RunEngine
import bluesky.callbacks as bc
import bluesky.callbacks.best_effort
from ophyd import sim

from cycler import cycler

import bact2
import bact2.bluesky.hacks.callbacks
from bact2.bluesky.hacks.callbacks import LivePlot, AxisWrapper

from bact2.ophyd.devices.raw import steerers, bpm
from bact2.ophyd.utils.preprocessors.CounterSink import CounterSink

from bact2.ophyd.devices.pp.bpm import BPMStorageRing



import numpy as np

class OffsetPlot( LivePlot ):
    def update_caches(self, x, y):
        """Just show the change
        """
        # Scale the current
        offset = -0.1281

        dx = x - offset
        dy = y - offset

        t_max = 3
        scale =1e3
        sdx = dx / t_max * scale
        sdy = dy / t_max * scale

        return super().update_caches(sdx, sdy)


def main():
    # Repeat the measurement 5 times

    n_meas = 5
    cs = CounterSink(name = "count_bpm_reads", delay = .2)
    repeat = cycler(cs, range(n_meas))


    col = steerers.SteererCollection(name=  "cs")
    steerer = col.steerers.vs2p1d1r

    print(steerer.name)
    det = [steerer]

    bec = bc.best_effort.BestEffortCallback()

    RE = RunEngine({})
    RE.log.setLevel("DEBUG")
    RE.log.setLevel("INFO")
    col.setLogger(RE.log)



    RE.subscribe(bec)
    install_qt_kicker()
    RE.waiting_hook = ProgressBarManager()



    col.set( 'hs1pd1r')
    bpm = BPMStorageRing(name = "bpm")
    if not bpm.connected:
        bpm.wait_for_connection()

    # dev = col.selected_steerer.dev
    dev = col.steerers.hs1pd1r.dev
    det = [
        bpm,
        dev.readback,
        dev.readback,
        col.sel_readback,
        col.sel_setpoint,
    ]

    current_offset = dev.readback.get()

    current_vals = np.array([0, 1, -1, 0])
    currents = current_vals * 1e-3 + current_offset
    steerer_steps = cycler(dev, currents)

    f = plt.figure(1, [8, 6])
    ax1 = plt.subplot(111)
    ax1 = AxisWrapper(ax1)


    RE(bp.scan_nd(det, steerer_steps * repeat),
       [OffsetPlot(
           #"cs_sel_readback", "cs_sel_setpoint",
           'cs_steerers_hs1pd1r_dev_readback',
           'cs_steerers_hs1pd1r_dev_setpoint',
           ax = ax1,
           marker = '.')]
       )
    # RE(bp.scan(det, dev, -10e-3 + current_offset, 10e-3 + current_offset, 2),[

if __name__ == '__main__':
    plt.ion()
    main()
    plt.ioff()
    plt.show()
