'''Comparison of single BPM panel data to Packed BPM panel data

BESSY II ring provides BPM data as packed data. These contain the
data of all BPM readings. These data is provided as
:class:`BPMStorageRing`.

Additionally each individual BPM can be accessed by a separate panel data.
Access to these data is provided by :class:`BPMCollection`.

This script provides a visual comparison of the two data access.
'''
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.utils import ProgressBarManager, install_qt_kicker
import bluesky.plans as bp

from ophyd import Component as Cpt, Device, Signal
from ophyd.status import AndStatus, Status

from bact2.ophyd.devices.pp.bpm import BPMStorageRing
from bact2.ophyd.devices.pp.bpm.bpm_single import BPMCollectionForComparison

from bact2.bluesky.live_plot import line_index, bpm_plot
import numpy as np


class BPMComparison( Device ):
    '''Calculate the difference between storage ring and the collection

    '''
    pck = Cpt(BPMStorageRing, name = 'packed')
    col = Cpt(BPMCollectionForComparison, name = 'collection')
    diff_x = Cpt(Signal, name = 'diff_x', value = [])
    diff_y = Cpt(Signal, name = 'diff_y', value = [])
    scale = Cpt(Signal, name = 'scale', value = 1.0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.col.names.value = [x.lower() for x in self.pck.waveform.names.value]

    def updateDifference(self):
        wv = self.pck.waveform
        dx = wv.x.pos.value - self.col.x.value
        dy = wv.y.pos.value - self.col.y.value

        scale = self.scale.value
        self.diff_x.value = dx * scale
        self.diff_y.value = dy * scale

    def trigger(self):
        stat_pck = self.pck.trigger()
        stat_trace = Status()

        def trigger_collection():
            nonlocal stat_trace
            stat_col = self.col.trigger()
            stat_col.add_callback(self.updateDifference)
            stat_trace.success = stat_col.success
            stat_trace._finished()

        stat_pck.add_callback(trigger_collection)
        stat = AndStatus(stat_pck, stat_trace)
        return stat

def main():

    bpm = BPMComparison(Device, name = 'cmp')

    # Let's test if we are playing with offset
    # bpm.pck.waveform.x.offset.value = 0
    # bpm.pck.waveform.y.offset.value = 0

    # If all variable names are required to be seen ...
    # bpm.summary()

    RE = RunEngine({})
    bec = BestEffortCallback()
    RE.subscribe(bec)
    install_qt_kicker()
    RE.waiting_hook = ProgressBarManager()

    fig1 = plt.figure(1, figsize=[16, 12])
    ax_x  = plt.subplot(211)
    ax_dx = plt.subplot(212)

    fig2 = plt.figure(2, figsize=[16, 12])
    ax_y  = plt.subplot(211)
    ax_dy = plt.subplot(212)

    bpm_names = bpm.pck.waveform.names.value
    bpm_positions = bpm.pck.waveform.ds.value

    class BPMComparisonPlot( bpm_plot.BPMComparisonPlot):
        def __init__(self, *args, **kwargs):
            kwargs.setdefault('bpm_names', bpm_names)
            kwargs.setdefault('bpm_positions', bpm_positions)
            super().__init__(*args, **kwargs)

    det = [bpm]

    ds_name = 'cmp_pck_waveform_ds'
    plots  = [
        BPMComparisonPlot("cmp_pck_waveform_x_pos", ds_name, ax = ax_x, legend_keys = ['packed']),
        BPMComparisonPlot("cmp_pck_waveform_y_pos", ds_name, ax = ax_y, legend_keys = ['packed']),
        BPMComparisonPlot("cmp_col_x", ds_name, ax = ax_x, legend_keys = ['single']),
        BPMComparisonPlot("cmp_col_y", ds_name, ax = ax_y, legend_keys = ['single']),
        BPMComparisonPlot("cmp_diff_x", ds_name, ax = ax_dx, legend_keys = ['diff']),
        BPMComparisonPlot("cmp_diff_y", ds_name, ax = ax_dy, legend_keys = ['diff']),
    ]

    RE(bp.count(det, 10), plots)


if __name__ == '__main__':
    plt.ion()
    main()
    plt.ioff()
    plt.show()
