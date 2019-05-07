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

from bact2.ophyd.devices.raw import multiplexer, quad_list
from bact2.ophyd.utils.preprocessors.CounterSink import CounterSink



class SelectorPlot(LivePlot):
    def update_caches(self, x, y):
        """Just show the change
        """
        # Scale the current
        dev = y - x
        return super().update_caches(x, dev)



def main():

    n_meas = 5


    cs = CounterSink(name = "count_bpm_reads", delay = .2)
    repeat = cycler(cs, range(n_meas))

    mux = multiplexer.Multiplexer(name = "mux")
    if not mux.connected:
        mux.wait_for_connection()

    #print(mux.activate)
    #print(dir(mux.activate))
    #print(dir(mux.activate.pcs))
    #return

    loop_over_quads = cycler(mux.selector, quad_list.quadrupoles)
    # loop_over_quads = loop_over_quads[:5]

    print(mux)
    det = [mux.selector.selected, mux.selector.readback]
    for d in det:
        print (d.name)

    bec = bc.best_effort.BestEffortCallback()

    RE = RunEngine({})
    #RE.log.setLevel("DEBUG")
    RE.log.setLevel("INFO")
    #print(dir(bpm))
    mux.selector.mux_switch_validate.setLogger(RE.log)
    mux.selector.setLogger(RE.log)

    RE.subscribe(bec)
    install_qt_kicker()
    RE.waiting_hook = ProgressBarManager()

    # serializer = Serializer('localhost',9200)
    # RE.subscribe(serializer)

    f = plt.figure(1, [20, 6])
    ax1 = plt.subplot(131)
    ax2 = plt.subplot(132)
    ax3 = plt.subplot(133)

    ax1 = AxisWrapper(ax1)
    ax2 = AxisWrapper(ax2)
    ax3 = AxisWrapper(ax3)

    RE(bp.scan_nd(det, loop_over_quads * repeat),
       [SelectorPlot("mux_selector_selected_num", "mux_selector_setpoint_num",  ax = ax1, marker = '.'),
        LivePlot("mux_selector_set_time", "mux_selector_setpoint_num",   ax = ax2, marker = '.'),
       LivePlot("mux_selector_last_wait", "mux_selector_setpoint_num",   ax = ax3, marker = '.')]

    )



if __name__ == '__main__':
    plt.ion()
    main()
