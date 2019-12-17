"""Measure the response matrix
"""
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

from bluesky.utils import ProgressBarManager, install_qt_kicker
from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback


from bact2.ophyd.devices.raw import steerers
from bact2.ophyd.devices.pp.bpm import BPMStorageRing
from bact2.bluesky.live_plot import line_index
from bact2.bluesky.live_plot.bpm_plot import BPMOffsetPlot, BPMOrbitOffsetPlot
from bact2.bluesky.plans.loop_steerers import loop_steerers


# from bact2.suitcase.serializer import Serializer
from databroker import Broker






def main():
    """step all steerers and read the bpms

    Main steps to measure the response matrix
    """
    col = steerers.SteererCollection(name = "sc")
    bpm = BPMStorageRing(name = "bpm")



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

    plots = [bpm_x, bpm_y, bpm_s,  bpm_x_o, bpm_y_o]


    RE = RunEngine({})
    # RE.log.setLevel("DEBUG")
    RE.log.setLevel("INFO")


    bec = BestEffortCallback()
    RE.subscribe(bec)

    pbar = ProgressBarManager()
    RE.waiting_hook = pbar


    db = Broker.named('light')
    RE.subscribe(db.insert)

    # serializer = Serializer()
    # s_id = RE.subscribe(serializer)



    RE.log.info('Starting to execute plan')
    det = [bpm, col.selected, col.sel.dev]

    h_st = steerers.horizontal_steerer_names
    v_st = steerers.vertical_steerer_names

    num = 2

    try_scan = False

    if try_scan:
        h_st = h_st[:2]
        v_st = v_st[:2]
        num = 1


    md = {
        'operator' : 'Pierre Begemothovitsch',
        'target' : 'loco development',
        'step' : 'testing data base storge',
        'try_scan' : try_scan,
        'comment' : 'first try to scan over all steerers and inject it into the database'
    }

    runs = RE(
        loop_steerers(det, col, horizontal_steerer_names = h_st, vertical_steerer_names = v_st, num_readings = num,
                      current_val_horizontal = current_val_horizontal, current_val_vertical = current_val_vertical,
        ),
        plots,
        md = md
    )
    RE.log.info('Executed runs {}'.format(runs))

    #serializer.closeServer()
    #RE.unsubscribe(s_id)
    #del serializer




if __name__ == '__main__':
    plt.ion()
    main()
    plt.ioff()
    plt.show()
