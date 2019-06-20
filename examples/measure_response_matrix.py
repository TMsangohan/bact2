"""Measure the response matrix
"""

import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

from bluesky.utils import ProgressBarManager, install_qt_kicker
from bluesky import RunEngine
from bluesky import plan_stubs as bps, preprocessors as bpp, callbacks as bc
import bluesky.callbacks.best_effort


from bact2.ophyd.devices.raw import steerers
from bact2.ophyd.devices.pp.bpm import BPMStorageRing
from bact2.bluesky.live_plot import line_index

import numpy as np

from bact2.suitcase.serializer import Serializer

def main():
    """step all steerers and read the bpms

    Main steps to measure the response matrix
    """
    col = steerers.SteererCollection(name = "sc")
    bpm = BPMStorageRing(name = "bpm")


    bec = bc.best_effort.BestEffortCallback()

    RE = RunEngine({})
    #RE.log.setLevel("DEBUG")
    RE.log.setLevel("INFO")


    RE.subscribe(bec)
    install_qt_kicker()
    RE.waiting_hook = ProgressBarManager()


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

    # Currents cycle ... respect hysteresis
    current_signs = np.array([0, 1, -1, 0])
    #--------------------------------------------------
    # Setting up the plots
    # Let"s have the actual x and y positions. Furthermore bpm
    # readings are read more than once. Let's have plots that
    # show how much these readings vary after the first reading
    # is made
    #

    # The figures for x and y ... on top of each other
    fig1 = plt.figure(1)
    ax1 = plt.subplot(211)
    ax1.grid(True)
    ax2 = plt.subplot(212)
    ax2.grid(True)
    # The stat ... if only would know what it means
    fig2 = plt.figure(2)
    ax3 = plt.subplot()

    bpm_x = line_index.PlotLineVsIndexOffset("bpm_waveform_pos_x", ax = ax1, legend_keys = ['x'])
    bpm_y = line_index.PlotLineVsIndexOffset("bpm_waveform_pos_y", ax = ax2, legend_keys = ['y'])
    bpm_s = line_index.PlotLineVsIndex("bpm_waveform_status", ax = ax3, legend_keys = ['stat'])

    # The offset plot
    fig1_1 = plt.figure(10)
    ax1_1 = plt.subplot(211)
    ax1_1.grid(True)
    ax1_2 = plt.subplot(212)
    ax1_2.grid(True)

    bpm_x_o = line_index.PlotLineVsIndexOffset("bpm_waveform_pos_x", ax = ax1, legend_keys = ['x'], color = 'c', linestyle = '--')
    bpm_y_o = line_index.PlotLineVsIndexOffset("bpm_waveform_pos_y", ax = ax2, legend_keys = ['y'], color = 'c', linestyle = '--')

    plots = [bpm_x, bpm_y, bpm_s,  bpm_x_o, bpm_y_o]


    def step_steerer(steerer, currents, detector, num_readings):
        """

        Todo:

        """
        # Using setpoint as reference ... assuming that this is the more
        # accurate value
        # make sure data are here
        yield from bps.trigger(steerer.setpoint)
        current_offset = steerer.setpoint.get()
        RE.log.info('Using steerer offset {:.5f}'.format(current_offset))

        for d_current in currents:
            t_current = d_current + current_offset
            RE.log.info('Setting steerer to I = {:.5f} = {:.5f} + {:.5f}'.format(t_current, current_offset, d_current))
            yield from bps.mv(steerer.setpoint, t_current)

            # Let's check if the first reading of the bpm is really useful
            # I guess first reading is too fast!
            # So first let's clear the offset plots
            [p.clearOffset() for p in (bpm_x_o, bpm_y_o)]
            for i in range(num_readings):
                yield from bps.trigger_and_read(detector)

    def loop_steerers(detectors, col, num_readings = 1, md = None,
                      horizontal_steerers = None, vertical_steerers = None):
        """
        """
        col_info = [col.selected.name, col.sel.name]
        _md = {'detectors': [det.name for det in detectors] + col_info,
              'num_readings': num_readings,
              'plan_args': {'detectors': list(map(repr, detectors)), 'num_readings': num_readings},
              'plan_name': 'response_matrix',
              'hints': {}
        }
        _md.update(md or {})


        assert(horizontal_steerers is not None)
        assert(vertical_steerers   is not None)

            
        RE.log.info('Starting run_all')

        @bpp.stage_decorator(list(det) + [col])
        @bpp.run_decorator(md=_md)
        def _run_all():
            """Iterate over vertical and horizontal steerers

            Get 
            """            
            # Lets do first the horizontal steerers and afterwards
            # lets get all vertial steerers

            currents = current_val_horizontal * current_signs
            
            for name in horizontal_steerers:
                name = name.lower()
                RE.log.info('Selecting steerer {}'.format(name))
                yield from bps.mv(col, name)
                yield from step_steerer(col.sel.dev, currents, det, num_readings)
                
            currents = current_val_vertical * current_signs
            for name in steerers.vertical_steerers[:2]:
                name = name.lower()
                RE.log.info('Selecting steerer {}'.format(name))
                yield from bps.mv(col, name)
                yield from step_steerer(col.sel.dev, currents, det, num_readings)


                
        return (yield from _run_all())

    bec = bc.best_effort.BestEffortCallback()

    pbar = ProgressBarManager()
    RE.waiting_hook = pbar


        
    serializer = Serializer()
    s_id = RE.subscribe(serializer)


    
    RE.log.info('Starting to execute plan')
    det = [bpm, col.selected, col.sel.dev]

    h_st = steerers.horizontal_steerers
    v_st = steerers.vertical_steerers

    try_scan = False

    num = 2
    if try_scan:
        h_st = h_st[:1]
        v_st = v_st[:1]
        num = 1
    

    runs = RE(loop_steerers(det, col, horizontal_steerers = h_st, vertical_steerers = v_st, num_readings = num), plots)
    RE.log.info('Executed runs {}'.format(runs))
    serializer.closeServer()
    RE.unsubscribe(s_id)
    del serializer




if __name__ == '__main__':
    plt.ion()
    main()
    plt.ioff()
    plt.show()
