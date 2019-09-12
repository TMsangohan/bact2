'''Display vacuum in the vsr straight together with the current and the life time

Uses the measured lifetime
'''
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

from bluesky.utils import ProgressBarManager, install_qt_kicker
from bluesky import RunEngine, suspenders
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.callbacks import LiveTable, LivePlot
import bluesky.plans as bp
import bluesky.plan_stubs as bps

import os.path
prefix = '/net/nfs/srv/MachinePhysics/MachineDevelopment/schnizer/github'
filename = os.path.join(prefix, 'vsr_straight')

# import databroker
# from databroker import Broker
from bact2.ophyd.devices.raw import beam, topup_engine, vacuum, life_time
from bact2.ophyd.devices.pp  import life_time as lt_pp



def main():

    bm = beam.BeamCurrentTriggered(name = 'beam')
    lt  = life_time.LifeTime(name = 'lt')
    ltm = lt_pp.LifetimeDevice(name = 'lt_dev')

    vac = vacuum.VacuumSensor('VMC3VS2R', name = 'vsr_straight')
    topup = topup_engine.TopUpEngine(name = 'topup')

    install_qt_kicker()
    RE = RunEngine({})

    # print('Saving to file {}'.format(filename))
    # db = Broker.named(filename)

    #RE.log.setLevel('INFO')
    #RE.log.setLevel('DEBUG')
    bec = BestEffortCallback()
    RE.subscribe(bec)
    # RE.subscribe(db.insert)

    det = [bm, lt, vac, ltm]
    ax = plt.gca()

    f = plt.figure(num = 1, figsize=[8,6])
    ax1 = plt.subplot(311)
    ax2 = plt.subplot(312)
    ax3 = plt.subplot(313)


    sufficent_time = suspenders.SuspendFloor(topup.next_injection, 2,  resume_thresh=11)
    RE.install_suspender(sufficent_time)

    # Delay by current reading
    RE(bp.count(det, num=5000, delay = 0),
       [
           LivePlot('vsr_straight_pressure',   x='time', ax = ax1, legend_keys = ['vac']),
           #LivePlot('lt_life_time_10',         x='time', ax = ax2, legend_keys = ['lt10']),
           LivePlot('lt_dev_life_time_lt',     x='time', ax = ax2, legend_keys = ['lt']),
           # LivePlot('lt_dev_life_time_lt_err', x='time', ax = ax2, legend_keys = ['lt_err'], marker = '.'),
           LivePlot('beam_readback',           x='time', ax = ax3, legend_keys = ['beam current']),
       ])

if __name__ == '__main__':
    plt.ion()
    main()
    plt.ioff()
    plt.show()
