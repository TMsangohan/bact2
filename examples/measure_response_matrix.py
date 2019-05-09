import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from cycler import cycler

import bluesky.plans as bp
import bluesky.plan_stubs as bps
from bluesky.utils import ProgressBarManager
from bluesky.utils import install_qt_kicker

from bluesky import RunEngine
import bluesky.callbacks as bc
import bluesky.callbacks.best_effort


import bact2
import bact2.bluesky.hacks.callbacks
from bact2.bluesky.hacks.callbacks import LivePlot, AxisWrapper

from bact2.ophyd.devices.raw import steerers

import bact2
import bact2.bluesky.hacks.callbacks
from bact2.bluesky.hacks.callbacks import LivePlot
from bact2.ophyd.devices.pp.bpm import BPMStorageRing
import numpy as np


def main():

    col = steerers.SteererCollection(name = "sc")
    steerer_names = [t[0] for t in steerers.t_steerers]

    bpm = BPMStorageRing(name = "bpm")
    if not bpm.connected:
        bpm.wait_for_connection()

    bec = bc.best_effort.BestEffortCallback()

    RE = RunEngine({})
    #RE.log.setLevel("DEBUG")
    RE.log.setLevel("INFO")



    RE.subscribe(bec)
    install_qt_kicker()
    RE.waiting_hook = ProgressBarManager()



    currents = (0, 1, -1, 0)
    current_vals = np.array([0, 1, -1, 0])

    bpm_det = [bpm]

    def step_steerer(steerer):
        nonlocal currents

        current_offset = steerer.readback.get()
        print(current_offset)
        currents = current_vals * 1e-3 + current_offset

        for t_current in currents:
            yield from bps.mv(steerer, t_current)
            det = [col.selected, col.selected_steerer.dev.readback] + bpm_det
            yield from bp.count(det)

    def run_all():
        for name in steerer_names:
            yield from bps.mv(col, name)
            yield from bps.trigger(col.selected_steerer.dev.readback)
            yield from step_steerer(col.selected_steerer.dev)

    RE(run_all(),
       [LivePlot("sc_selected_readback", "sc_selected_setpoint",   ax = None, marker = '.')]
           )



if __name__ == '__main__':
    plt.ion()
    main()
    plt.ioff()
    plt.show()
