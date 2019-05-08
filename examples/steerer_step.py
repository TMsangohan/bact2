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

def main():
    # Repeat the measurement 5 times

    col = steerers.SteererCollection(name=  "cs")
    steerer = col.steerers.hs4p1d6r
    print(steerer.name)
    det = [steerer]

    bec = bc.best_effort.BestEffortCallback()

    RE = RunEngine({})
    #RE.log.setLevel("DEBUG")
    RE.log.setLevel("INFO")

    currents = (0, 1, -1, 0)
    steerer_steps = cycler(steerer, currents)


    RE.subscribe(bec)
    install_qt_kicker()
    RE.waiting_hook = ProgressBarManager()

    def step_steerer():
        nonlocal currents
        for t_current in currents:
            print("Current to run over ")
            # yield from bps.mv(steerer.dev, t_current)
            yield from bp.count([steerer.dev.readback])

    RE(step_steerer(),
           LivePlot("a_steerer_dev_readback", "a_steerer_dev_setpoint",   ax = None, marker = '.'),
           )

if __name__ == '__main__':
    main()
