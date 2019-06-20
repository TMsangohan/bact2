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

import sys
import os
sys.path.append('/opt/OPI/MachinePhysics/MachineDevelopment/mertens/github-repos/suitcase-elasticsearch')
from getpass import getpass
import elasticsearch
from sshtunnel import SSHTunnelForwarder
from suitcase.elasticsearch import Serializer

def main():
    """step all steerers and read the bpms

    Main steps to measure the response matrix
    """
    col = steerers.SteererCollection(name = "sc")
    bpm = BPMStorageRing(name = "bpm")

    steerer_names = col.steerers.component_names

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

    current_val = ihs #/ 10.0

    # Currents cycle ... respect hysteresis
    current_signs = np.array([0, 1, -1, 0])
    currents = current_val * current_signs

    det = [bpm]
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

    bpm_x_o = line_index.PlotLineVsIndexOffset("bpm_waveform_pos_x", ax = ax1_1, legend_keys = ['x'])
    bpm_y_o = line_index.PlotLineVsIndexOffset("bpm_waveform_pos_y", ax = ax1_2, legend_keys = ['y'])

    plots = [bpm_x, bpm_y, bpm_s,  bpm_x_o, bpm_y_o]


    def step_steerer(steerer, detector, num_readings):
        """

        Todo:

        """
        nonlocal currents

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

    def run_all(detectors, col, num_readings = 2, md = None):

        col_info = [col.selected.name, col.sel.name]
        _md = {'detectors': [det.name for det in detectors] + col_info,
              'num_readings': num_readings,
              'plan_args': {'detectors': list(map(repr, detectors)), 'num_readings': num_readings},
              'plan_name': 'response_matrix',
              'hints': {}
        }
        _md.update(md or {})


        RE.log.info('Starting run_all')

        @bpp.stage_decorator(list(det) + [col])
        @bpp.run_decorator(md=_md)
        def _run_all():
            for name in steerer_names[:2]:
                RE.log.info('Selecting steerer {}'.format(name))
                yield from bps.mv(col, name)
                yield from step_steerer(col.sel.dev, det, num_readings)

        yield from _run_all()

    bec = bc.best_effort.BestEffortCallback()

    pbar = ProgressBarManager()
    RE.waiting_hook = pbar

    server = None
    store = True
    if store:
        MONGO_HOST = "skylab.acc.bessy.de"
        MONGO_DB = "StorageRing"
        #login = getpass()
        #pwd = getpass()
        MONGO_USER = os.environ['MONGO_USER']
        MONGO_PASS = os.environ['MONGO_PASS']

        server = SSHTunnelForwarder(
	    MONGO_HOST,
	    ssh_username=MONGO_USER,
	    ssh_password=MONGO_PASS,
	    remote_bind_address=('0.0.0.0', 9200)
        )

        # START SSH TUNNEL SERVER
        server.start()

        serializer = Serializer('localhost', server.local_bind_port)
        RE.subscribe(serializer)


    
    RE.log.info('Starting to execute plan')
    
    try:
        RE(run_all(det, col), plots)
        plt.ioff()
        plt.show()
    finally:
        RE.log.info('Finished executing plan lets go')
        if server is not None:
            RE.log.info('Closing Server: still alive {} ?'.format(server.is_alive))
            server.close()
            RE.log.info('Stoping server: still alive {} ?'.format(server.is_alive))
            server.stop()
            RE.log.info('Stopped Server: still alive {} ?'.format(server.is_alive))




if __name__ == '__main__':
    # plt.ion()
    main()
    # plt.ioff()
    # plt.show()
