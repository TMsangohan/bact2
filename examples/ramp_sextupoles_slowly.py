#!/usr/bin/env python
# coding: utf-8
import matplotlib
matplotlib.use('Qt4Agg')

from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO, PVPositionerPC, PVPositioner, Signal

import bluesky.plans as bp
from bluesky import RunEngine
from bluesky.utils import install_kicker
from bluesky.callbacks import LivePlot
from bluesky.callbacks.best_effort import BestEffortCallback

# from databroker import Broker

import matplotlib.pyplot as plt
import numpy as np
import functools

class PowerConverter(PVPositioner):
    setpoint = Cpt(EpicsSignal,   ':set')
    readback = Cpt(EpicsSignalRO, ':rdbk')
    
    # If used as PVPositioner .... 
    # but study first how much the offset has to be
    # This values i actually in range ...
    done    =  Cpt(EpicsSignalRO, ':stat8')


class SextupolePC(PowerConverter):
    def __init__(self, *args, name = None, **kwargs):
        kwargs.setdefault('settle_time', .1)
        super().__init__(*args, name = name,  **kwargs)
    
class SextupoleCollection(Device):
    s3pdr = SextupolePC('S3PDR', name = 's3pdr')
    s3ptr = SextupolePC('S3PTR', name = 's3ptr')
    s4pdr = SextupolePC('S4PDR', name = 's4pdr')
    s4ptr = SextupolePC('S4PTR', name = 's4ptr')




def main():
    sp = SextupoleCollection(name = 'sc')

    power_converters = [
        sp.s3pdr, sp.s3ptr, 
        sp.s4pdr, sp.s4ptr
    ]
    sp.s3pdr.settle_time = .2
    print(sp.s3pdr.settle_time)

    install_kicker()
    RE = RunEngine({})
    bec = BestEffortCallback()
    RE.subscribe(bec)


    # temp is a yaml file describing which kind of broker
    # db = Broker('temp')
    # RE.subscribe(db.insert)
    
    # A first plot test ... 
    plt.ion()
    f = plt.figure(1)
    ax = plt.gca()

    
    uids = RE(bp.count(power_converters, 3, delay=[.2, .5]), LivePlot('s3pdr_setpoint', 'time', ax = ax))
    
    uids = RE(bp.count(power_converters, 10, delay=1), LivePlot('s3pdr_setpoint', 'time', ax = ax))

    
    # These data is now in the data broker
    vals = [(pc.setpoint.value, pc.readback.value) for pc in power_converters]

    # That's how these should be retrieved from the data broker
    # last = db[-1]
    def getvals(pc):
        name = pc.name
        t_set = name + '_setpoint'
        t_rbk = name + '_readback'
        r = (last[t_set], last[t_rbk])
        return r
    # vals = [getvals(pc) for pc in power_converters]]

    vals = np.array(vals)
    
    print(vals)

    # Lets go a step a head and ramp ...
    # I assume all are ramped by the same manner
    
    f = plt.figure(2)
    ax1 = plt.subplot(221)
    ax2 = plt.subplot(222)
    ax3 = plt.subplot(223)
    ax4 = plt.subplot(224)


    plots = [
        LivePlot('s3pdr_setpoint', ax = ax1),
        LivePlot('s3ptr_setpoint', ax = ax2),
        LivePlot('s4pdr_setpoint', ax = ax3),
        LivePlot('s4ptr_setpoint', ax = ax4),
    ]

    dI = .1
    start_currents = vals[:, 0]
    end_currents   = start_currents + dI

    # Relative scan does not work .... why I do not know
    # I don't want to use epics variables but rather the
    # device itself
    #
    # Now make the argument list
    #     sextupole 1 start current 1 end current 1
    #     sextupole 2 start current 2 end current 2
    #     .
    #     .
    args = np.array([power_converters, start_currents, end_currents])
    args = args.T.ravel()
    
    plan = functools.partial(bp.scan, power_converters,*args, num = 100)
    RE.log.setLevel('DEBUG')

    # Well better only activate it during machine commissioning
    # RE(plan())


if __name__ == '__main__':
    plt.ion()
    main()
    plt.ioff()
    print("Done")
    plt.show()






