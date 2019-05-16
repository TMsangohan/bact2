"""read all steeres peridically and plot their set and readback data
"""
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

from bact2.ophyd.devices.raw import steerers
from bact2.ophyd.devices.pp.bpm import BPMStorageRing
from collections import OrderedDict


import numpy as np

class SteererNameToNum:
    def __init__(self):
        self._steerers_dic = OrderedDict()
        self.steerer_names = []


    def reSortSteerers(self):
        names = [n for n in self._steerers_dic.keys()]
        names.sort()
        self.steerer_names = names

        cnt = 0
        for name in self.steerer_names:
            cnt += 1
            self._steerers_dic[name] = cnt

    def addName(self, name):
        try:
            self._steerers_dic[name]
        except KeyError:
            self._steerers_dic[name] = None
            self.reSortSteerers()

    def nameToNum(self, name):
        cnt = self._steerers_dic[name]
        return cnt

st_n2n = SteererNameToNum()
class SteererPlotValue( LivePlot ):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._steerer_vals = OrderedDict()
        self.scale_value = 1
        self.counter = 0

    def update_one(self, name, val):
        st_n2n.addName(name)
        try:
            self._steerer_vals[name]
        except KeyError:
            self._steerer_vals[name] = []

        entry = self._steerer_vals[name]
        entry.append(val)

    def update_caches(self, name, val):
        """Just show the change
        """
        self.update_one(name, val)

        self.counter += 1
        if self.counter % 100 != 1:
            pass
            #return

        cnt_data = []
        val_data = []

        names = st_n2n.steerer_names
        assert(len(names) > 0)
        for name in names:
            vals = self._steerer_vals[name]
            vals = np.array(vals)
            mval = vals.mean()
            mval = vals[0]
            idx  =  st_n2n.nameToNum(name)
            # Conversion to list and back to array to avoid
            # overwriting list stored in self._sterrer_vals
            # nan to signal to matplotlib to stop the line
            for val in (vals.tolist() + [np.nan]):
                cnt_data.append(idx)
                dval = val - mval
                dval = dval * self.scale_value
                val_data.append(dval)
        self.x_data = cnt_data
        self.y_data = val_data


def main():
    # Repeat the measurement 5 times

    RE = RunEngine({})
    RE.log.setLevel("INFO")

    n_meas = 20
    cs = sim.motor
    repeat = cycler(cs, range(n_meas))

    col = steerers.SteererCollection(name=  "cs")

    steerer_names = [x[0] for x in steerers.t_steerers]
    steerer_names = col.steerers.component_names
    cyc_st = cycler(col, steerer_names)
    if not col.connected:
        col.wait_for_connection()

    det = [col.sel.dev.setpoint, col.sel.dev.readback]
    bec = bc.best_effort.BestEffortCallback()


    RE.subscribe(bec)
    install_qt_kicker()
    RE.waiting_hook = ProgressBarManager()


    f = plt.figure(1, [8, 6])
    ax1 = plt.subplot(211)
    ax1 = AxisWrapper(ax1)
    ax2 = plt.subplot(212)
    ax2 = AxisWrapper(ax2)


    set_plt  = SteererPlotValue('cs_sel_dev_setpoint', 'cs_selected',  marker = '.', color='b', linestyle = '--', ax = ax1, linewidth = .5, legend_keys = ['set'])
    set_plt.scale_value = 1000 * 100
    rdbk_plt = SteererPlotValue('cs_sel_dev_readback', 'cs_selected',  marker = '.', color='c', linestyle = '-', ax = ax2, legend_keys = ['rdbk'])
    rdbk_plt.scale_value = 1000 * 100
    plotters = [set_plt, rdbk_plt]
    RE(bp.scan_nd(det, repeat * cyc_st), plotters)
    # RE(bp.scan(det, dev, -10e-3 + current_offset, 10e-3 + current_offset, 2),[

if __name__ == '__main__':
    plt.ion()
    main()
    plt.ioff()
    plt.show()
