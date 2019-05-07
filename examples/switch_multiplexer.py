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
from bact2.bluesky.hacks.callbacks import LivePlot

from bact2.ophyd.devices.raw import multiplexer, quad_list



def main():

    n_meas = 1

    cs = sim.motor
    repeat = cycler(cs, range(n_meas))

    mux = multiplexer.Multiplexer(name = "mux")
    if not mux.connected:
        mux.wait_for_connection()

    #print(mux.activate)
    #print(dir(mux.activate))
    #print(dir(mux.activate.pcs))
    #return

    loop_over_quads = cycler(mux.selector, quad_list.quadrupoles)
    loop_over_quads = loop_over_quads[:5]

    print(mux)
    det = [mux.selector]
    for d in det:
        print (d.name)

    bec = bc.best_effort.BestEffortCallback()

    RE = RunEngine({})
    #RE.log.setLevel("DEBUG")
    # RE.log.setLevel("INFO")
    #print(dir(bpm))
    mux.selector.mux_switch_validate.setLogger(RE.log)
    mux.selector.setLogger(RE.log)

    RE.subscribe(bec)
    install_qt_kicker()
    RE.waiting_hook = ProgressBarManager()

    # serializer = Serializer('localhost',9200)
    # RE.subscribe(serializer)

    RE(bp.scan_nd(det, repeat * loop_over_quads))



if __name__ == '__main__':
    plt.ion()
    main()
