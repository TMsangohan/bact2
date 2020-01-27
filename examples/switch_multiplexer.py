import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

from bact2.ophyd.devices.raw import multiplexer, quad_list
from bact2.ophyd.utils.preprocessors.CounterSink import CounterSink

import bluesky.plans as bp
from bluesky.utils import ProgressBarManager, install_qt_kicker
from bluesky.callbacks import LivePlot, LiveTable
from bluesky import RunEngine

from ophyd import sim
from cycler import cycler


class SelectorPlot(LivePlot):
    def update_caches(self, x, y):
        """Just show the change
        """
        # Scale the current
        diff = y - x
        return super().update_caches(x, diff)


def main():

    n_meas = 1
    cs = CounterSink(name = "count_bpm_reads", delay = .2)
    repeat = cycler(cs, range(n_meas))

    mux = multiplexer.Multiplexer(name = "mux")
    if not mux.connected:
        mux.wait_for_connection()

    loop_over_quads = cycler(mux.selector, quad_list.quadrupoles)

    det = [mux.selector, mux.power_converter]
    det = [mux]
    for d in det:
        print (d.name)


    RE = RunEngine({})
    # RE.log.setLevel("DEBUG")
    # RE.log.setLevel("INFO")

    mux.selector.mux_switch_validate.setLogger(RE.log)
    mux.selector.setLogger(RE.log)

    install_qt_kicker()


    f = plt.figure(1, [20, 6])
    ax1 = plt.subplot(131)
    ax2 = plt.subplot(132)
    ax3 = plt.subplot(133)

    # values should be always 0
    sel_p = SelectorPlot("mux_selector_selected_num", "mux_selector_setpoint_num", ax=ax1, marker='.')
    # how long did it take to set the value
    dt_p     =  LivePlot("mux_selector_set_time",     "mux_selector_setpoint_num", ax=ax2, marker='.')
    # and how long was the last response to the set value
    dt_chk_p =  LivePlot("mux_selector_last_wait",    "mux_selector_setpoint_num", ax=ax3, marker='.')

    vars_for_lt = [
        mux.selector.selected_num, mux.selector.readback,
         mux.power_converter.setpoint, mux.power_converter.readback
    ]

    lt = LiveTable(vars_for_lt, default_prec=10)

    callbacks = [sel_p, dt_p, dt_chk_p, lt]
    RE(bp.scan_nd(det, loop_over_quads * repeat), callbacks)



if __name__ == '__main__':
    plt.ion()
    main()
    plt.ioff()
    plt.show()
