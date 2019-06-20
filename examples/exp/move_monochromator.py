import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

import bluesky.plans as bp
import bluesky.plan_stubs as bps
from bluesky.utils import ProgressBarManager
from bluesky.utils import install_qt_kicker
#from bluesky.utils import install_nb_kicker

from bluesky import RunEngine
import bluesky.callbacks as bc
import bluesky.callbacks.best_effort
from ophyd import sim

from .mono_chromator import Monochromator

from cycler import cycler


mc = Monochromator(name = 'mc')
if not mc.connected:
    mc.wait_for_connection()

RE = RunEngine({})
RE.log.setLevel("DEBUG")
RE.log.setLevel("INFO")

install_qt_kicker()
bec = bc.best_effort.BestEffortCallback()
RE.subscribe(bec)

det = [mc.dev]


#plt.ion()
# RE(bp.count(det, 5))

start = 13980
end   = 14420
n_points = 5 + 1
RE(bp.scan(det, mc.dev, start, end, n_points))
#plt.ioff()
#plt.show()
