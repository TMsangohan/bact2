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

import sys
sys.path.append('/home/tmerten/github-repos/')
# sys.path.append('/net/nfs/srv/MachinePhysics/MachineDevelopment/Mertens/github-repos/')
sys.path.append('/home/tmerten/gitlab-repos-hzb/suitcase-elasticsearch/')

# from suitcase.elasticsearch import Serializer

from bact2.ophyd.devices.pp.bpm import BPMStorageRing
import bact2
import bact2.bluesky.hacks.callbacks
from bact2.bluesky.hacks.callbacks import LivePlot, AxisWrapper

import numpy as np


class PlotLineVsIndex(LivePlot):
    """plot data versus index
    """
    def update_caches(self, x, y):
        ind = np.arange(len(y))
        self.x_data = ind.tolist()
        self.y_data = y.tolist()

class BPMLivePlot(PlotLineVsIndex):
    """Scale plot data
    """
    #: scale factor of y data
    #: mm/ mA
    scale_dep = 1
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_value = None

    def update_caches(self, x, y):
        # Scale to kHz
        if self.old_value is None:
            self.old_value = y
        dy = y - self.old_value
        super().update_caches(x, dy)



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
    ax1 = AxisWrapper(ax1)
    ax2 = AxisWrapper(ax2)
    fig1 = plt.figure(2)
    ax3 = plt.subplot()
    ax3 = AxisWrapper(ax3)
    RE(bp.scan_nd(det, sw_freq * repeat),
       [
           BPMLivePlot("bpm_waveform_pos_x", ax = ax1, legend_keys = ['x']),
           BPMLivePlot("bpm_waveform_pos_y", ax = ax2, legend_keys = ['y']),
           PlotLineVsIndex("bpm_waveform_status", ax = ax3, legend_keys = ['stat']),
       ]
    )


if __name__ == '__main__':
    plt.ion()
    main()
    plt.ioff()
    plt.show()
