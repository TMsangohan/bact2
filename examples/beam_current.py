"""Display beam current reading at BESSY II

Display the readings of the different current monitors

See :mod:` bact2.ophyd.devices.raw.beam` for a description of the
current monitors.

"""
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

from bluesky.utils import ProgressBarManager, install_qt_kicker
from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.callbacks import LiveTable, LivePlot
import bluesky.plans as bp
from ophyd.status import SubscriptionStatus


from bact2.ophyd.devices.raw import beam
import time
import numpy as np

class Beam( beam.Beam ):
    def trigger(self):
        """Ensure that new values have arrived
        """
        self.log.info('Triggering beam current reading')

        t0 = time.time()

        count = 0
        def cb(*args, **kwargs):
            '''Only the second reading seems to be a valid one?
            '''
            nonlocal t0, count
            count += 1

            t1 =  kwargs['timestamp']
            dt = t1 - t0
            txt = '{:.3f} Got args {} kwargs {}'.format(dt, args, kwargs)
            self.log.debug(txt)
            # print(txt)

            if count == 1:
                return False
            return True

        timeout = 3
        sig = self.current.readback
        # sig = self.current.cur1
        status = SubscriptionStatus(sig, cb, run = False, timeout = timeout)
        return status

class SourcePlot( LivePlot ):
    '''Liveplot saving last updated values

    Used by :class:`DiffPlot` to plot the difference of the
    dependent variable with respect to the data received by
    this variable
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ref_t = np.nan
        self.ref_val = np.nan

    def getRef(self):
        return self.ref_t, self.ref_val

    def update_caches(self, t, y):
        self.ref_t = t
        self.ref_val = y
        super().update_caches(t, y)

class DiffPlot( LivePlot ):
    '''Plot the difference to some updated values

    This version uses only the difference in y.
    Here the independent variable is assumed to be the time t,
    which seems to be the same for all the different current
    monitors.
    '''
    def __init__(self, *args, **kwargs):
        refplot = kwargs.pop('refplot')
        assert(callable(refplot.getRef))

        super().__init__(*args, **kwargs)
        self._refplot = refplot

    def update_caches(self, t, y):
        t_ref, y_ref = self._refplot.getRef()
        dt = t - t_ref
        dy = y - y_ref

        # print("dt {:.9f} dy {:.3f}".format(dt,dy))
        super().update_caches(t_ref, dy)


from bact2.ophyd.devices.raw import beam

def main():
    bm = Beam(name = 'beam')

    if not bm.connected:
        bm.wait_for_connection(timeout=2)

    install_qt_kicker()

    RE = RunEngine({})
    RE.log.setLevel('INFO')
    bec = BestEffortCallback()
    RE.subscribe(bec)

    fig = plt.figure(1)
    ax = plt.gca()
    fig = plt.figure(2)
    ax2 = plt.gca()

    det = [bm]

    # The current as displayed by the topup panel in red
    src_p = SourcePlot('beam_current_readback', x = 'time', ax = ax, marker='.', color = 'r')

    # The different raw current monitors in blue
    diff_p1 = DiffPlot('beam_current_cur1', refplot = src_p,  x = 'time', ax = ax2, marker='.', color = 'b')
    diff_p2 = DiffPlot('beam_current_cur2', refplot = src_p,  x = 'time', ax = ax2, marker='.', color = 'b')
    diff_p3 = DiffPlot('beam_current_cur3', refplot = src_p,  x = 'time', ax = ax2, marker='.', color = 'b')

    # The current monitors as used by topup in magenta
    diff_tp1 = DiffPlot('beam_current_topup1', refplot = src_p,  x = 'time', ax = ax2, marker='+', color = 'm')
    diff_tp2 = DiffPlot('beam_current_topup2', refplot = src_p,  x = 'time', ax = ax2, marker='+', color = 'm')

    # The plots as used by the PTB in green
    diff_ptb1 = DiffPlot('beam_current_ptb1', refplot = src_p,  x = 'time', ax = ax2, marker='x', color = 'g')
    diff_ptb2 = DiffPlot('beam_current_ptb2', refplot = src_p,  x = 'time', ax = ax2, marker='x', color = 'g')

    # Best effort callbacks
    beff_cbs = []
    # beff_cbs += [LiveTable(det)]
    beff_cbs += [src_p]
    beff_cbs += [diff_p1, diff_p2, diff_p3]
    beff_cbs += [diff_tp1, diff_tp2]
    beff_cbs += [diff_ptb1, diff_ptb2]

    RE(bp.count(det, 100), beff_cbs)


if __name__ == '__main__':
    plt.ion()
    main()
    plt.ioff()
    plt.show()
