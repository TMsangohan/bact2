"""Measure the response matrix
"""
import logging
# logging.basicConfig(level = 'INFO')
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

from bluesky.utils import ProgressBarManager, install_qt_kicker
from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.callbacks import LiveTable
from bluesky.suspenders import SuspendFloor
import bluesky.preprocessors as bpp

from bact2.ophyd.devices.raw import beam, steerers, tunes
from bact2.ophyd.devices.utils import book_keeping_dev
# from bact2.ophyd.devices.pp import steerer

from bact2.ophyd.devices.pp.bpm import BPMStorageRing
from bact2.ophyd.devices.utils.optimizers import LinearGradient, CautiousRootFinder
from bact2.bluesky.live_plot import line_index
from bact2.bluesky.live_plot.bpm_plot import BPMOffsetPlot, BPMOrbitOffsetPlot
from bact2.bluesky.plans.loop_steerers import loop_steerers


# from bact2.suitcase.serializer import Serializer
from databroker import Broker

import numpy as np


def main():
    """step all steerers and read the bpms

    Main steps to measure the response matrix
    """
    col = steerers.SteererCollection(name = "sc")
    bpm = BPMStorageRing(name = "bpm")
    tn = tunes.TuneMeasurement(name = 'tune')

    cr = CautiousRootFinder(name='cr')

    t_beam = beam.Beam(name = 'beam')

    # print(col.describe())
    # print(bpm.describe())
    # return

    install_qt_kicker()


    # These values are for standard operation mode and require to be checked
    # steerer current values as found in bessyIIinit

    # data from bessyIIinit
    # vertical steerer
    ivs = 0.07

    # ihbm = 0.14; %Nutzeroptik
    # ihs  = 0.07/3.;

    ihbm = 0.14/2  #%Nutzeroptik
    ihs  = 0.07/6. #; %14.06.10

    current_val_horizontal = ihs
    current_val_vertical = ivs

    #--------------------------------------------------
    # Setting up the plots
    # Let"s have the actual x and y positions. Furthermore bpm
    # readings are read more than once. Let's have plots that
    # show how much these readings vary after the first reading
    # is made
    #

    # The figures for x and y ... on top of each other
    fig1 = plt.figure(1, figsize=[16,12])
    # fig1 = plt.figure(1, figsize=[4,3])
    ax1 = plt.subplot(221)
    ax1.grid(True)
    ax2 = plt.subplot(222)
    ax2.grid(True)


    bpm_x = BPMOrbitOffsetPlot("bpm_waveform_x_pos", ax = ax1, legend_keys = ['x'])
    bpm_y = BPMOrbitOffsetPlot("bpm_waveform_y_pos", ax = ax2, legend_keys = ['y'])


    # The offset plot
    ax1_1 = plt.subplot(223)
    ax1_1.grid(True)
    ax1_2 = plt.subplot(224)
    ax1_2.grid(True)

    bpm_x_o = BPMOffsetPlot("bpm_waveform_x_pos", ax = ax1_1, legend_keys = ['x'], color = 'c', linestyle = '--')
    bpm_y_o = BPMOffsetPlot("bpm_waveform_y_pos", ax = ax1_2, legend_keys = ['y'], color = 'c', linestyle = '--')


    # The stat ... if only would know what it means
    fig2 = plt.figure(2)
    ax3 = plt.subplot()
    bpm_s = line_index.PlotLineVsIndex("bpm_waveform_status",      ax = ax3, legend_keys = ['stat'])

    bk_dev = book_keeping_dev.Bookkeeping(name='bk_dev')
    bk_dev.mode.value = 'startup'

    lt = LiveTable([col.selected, bk_dev.mode, bk_dev.current_offset, bk_dev.dI, bk_dev.scale_factor,  col.sel.dev.setpoint], default_prec=10)
    plots = [bpm_x, bpm_y, bpm_s,  bpm_x_o, bpm_y_o] + [lt]


    RE = RunEngine({})
    watch_beam = SuspendFloor(t_beam.current.readback, 1, resume_thresh = 2)
    RE.install_suspender(watch_beam)
    # RE.log.setLevel("DEBUG")
    RE.log.setLevel("INFO")


    bec = BestEffortCallback()
    # RE.subscribe(bec)

    pbar = ProgressBarManager()
    RE.waiting_hook = pbar


    db = Broker.named('light')
    RE.subscribe(db.insert)

    # serializer = Serializer()
    # s_id = RE.subscribe(serializer)

    # bm = beam.Beam(name = 'beam')
    # sd = bpp.SupplementalData(
    #    monitors = [bm]
    # )
    # RE.preprocessors.append(sd)

    RE.log.info('Starting to execute plan')
    det = [bpm,
           tn,
           col,
           # lg,
           # cr,
           #bk_dev
    ] #, col.selected, col.sel.dev]

    h_st = steerers.horizontal_steerer_names
    v_st = steerers.vertical_steerer_names


    n_st = len(h_st + v_st)
    num = 3
    repeat = 2
    try_scan = True

    n_st2 = n_st
    if try_scan:
        h_st = h_st[:2]
        v_st = v_st[:3]
        #v_st = []
        num = 2
        repeat = 1
        n_st2 = len(h_st + v_st)

    # Make all steerers setting back to last value in cast of stop is requested
    for name in h_st + v_st:
        st = getattr(col.steerers, name)
        st.set_back.value = True
        st.log = RE.log

    print(f'Total number of steeres {n_st} but  only executing using {n_st2}')

    comment = 'Data taking seems to work now. First run over all steerers (except for dipole steerers)'
    comment = '''Data taking seems to work now. That's why I had looked into trying to optimze
    the current steps. Now data taking starts to get useful.
    '''
    comment = 'trying to run enough points to estimate the non linearity'
    comment = 'trying to use difference between steerer setpoint and readback to go ahead'
    md = {
        'operator' : 'Pierre Begemothovitsch',
        'target' : 'loco development',
        'step' :  'development of code, upgrade to better readability',
        'try_scan' : try_scan,
        'comment' : comment

    }

    current_steps = np.array([0, .25,  .5,   .75,  1,
                                 .75,  .5,   .25,  0,
                                -.25, -.5,  -.75, -1,
                                -.75, -.5,  -.25,  0])
    # current_steps = np.array([0, .5, 1, .5, -.5, -1, -.5, 0])
    # current_steps = np.array([0, 1,  -1,  0])
    cr.log = RE.log

    for i in range(repeat):
        runs = RE(
            loop_steerers(det, col, horizontal_steerer_names = h_st, vertical_steerer_names = v_st, num_readings = num,
                          current_val_horizontal = current_val_horizontal, current_val_vertical = current_val_vertical,
                          current_steps = current_steps, dr_target=.2,
                          book_keeping_dev = bk_dev, root_finder=cr,
                          logger=RE.log
                          # linear_gradient=lg,
            ),
            plots,
            **md
        )
        txt = 'Cnt {} Executed runs {}'.format(repeat, runs)
        print(txt)
        RE.log.info(txt)

    #serializer.closeServer()
    #RE.unsubscribe(s_id)
    #del serializer




if __name__ == '__main__':
    plt.ion()
    main()
    plt.ioff()
    plt.show()
