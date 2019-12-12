import logging

# logging.basicConfig(level = 'INFO')

import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

from bact2.ophyd.devices.raw import booster_feedback, topup_engine, linac_gun
from ophyd import Device, Component as Cpt, EpicsSignalRO, Signal
from ophyd.status import SubscriptionStatus

from bluesky import plan_stubs as bps, preprocessors as bpp
from bluesky.utils import ProgressBarManager, install_qt_kicker
from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.callbacks import LivePlot


class SwitchFeedbackOnOff( Device ):
    '''Wait for injection finished

    Collection of devices for convienience in the plan below
    '''
    feedback   = Cpt(booster_feedback.BoosterFeedback, name = 'fb')
    topup      = Cpt(topup_engine.TopUpEngine,         name = 'tu')
    linac_gun  = Cpt(linac_gun.LinacGun,               name = 'lg')

    # A reasonable timeout ?
    timeout    = Cpt(Signal, value = 10 * 60)
    valid_data = Cpt(Signal, value = True)

    def trigger(self):
        '''Only return when a new bunch was received
        '''
        def cb(*args, **kwargs):
            value = kwargs['value']
            old_value = kwargs['old_value']
            timestamp = kwargs['timestamp']

            if value == 0:
                # No new injecton
                return False

            elif value == 1:
                return True

            else:
                raise AssertionError('Unexpected value {}'.format(value))

        dt = self.timeout.value
        stat_it = SubscriptionStatus(self.topup.injection_trigger, cb, run = False, timeout = dt)
        return stat_it


def check_pulses(dev, nb_set_val, repeat_not_made = 10, logger = None):
    '''Check if the requested number of pulses was submitted

    Todo:
        Rename function
    '''
    for cnt in range(repeat_not_made):
        yield from bps.trigger_and_read([dev])

        nb_gun = dev.linac_gun.timer_gun_pulses.value
        nb_gun = round(nb_gun)
        nb_gun = int(nb_gun)
        if nb_gun == nb_set_val:
            dev.valid_data.value = True
            break

        dev.valid_data.value = False
        fmt = 'Requested number of bunches {} but gun shot {}: repeating'
        logger.info(fmt.format(nb_set_val, nb_gun))

    else:
        fmt = 'Did not manage to get {} number of bunches in {} retries'
        raise AssertionError(fmt.format(nb_set_val, repeat_not_made))

def switch_feedback_one_step(dev, md = None, repeat_not_made = 10, logger = None):
    '''toggle feedback off or on

    Inject number of bunches from 1 ... 5 then switch the feedback on or off

    Todo:
        Rework function... switching should be moved one step up
        Rename function appropriately
    '''

    val = dev.feedback.x.active.value
    logger.info('Feedback x channel {} (active = 1)'.format(val))

    nb = dev.topup.number_of_bunches
    for nb_set_val in range(1, 5+1):

        logger.info('Setting number of bunches to {}'.format(nb_set_val))
        yield from bps.mv(nb, nb_set_val)
        yield from check_pulses(dev, nb_set_val, repeat_not_made = repeat_not_made, logger = logger)

    val = dev.feedback.x.active.value
    if val:
        set_val = 0
    else:
        set_val = 1

    # a time to wait for simplifing analysis
    yield from bps.sleep(5.0)
    yield from bps.mv(dev.feedback, set_val)

    val = dev.feedback.x.active.value
    val_z = dev.feedback.x.active.value
    logger.info('Switched Feedbacks. x channel now {} z channel now {} (active = 1)'.format(val, val_z))


def switch_feedback(dev, repeat=10, md = None, logger = None):
    '''

    Todo:
        Rename function
    '''
    _md = {
        'detectors' : [dev.name],
        'repeat' : repeat
    }
    _md.update(md or {})

    @bpp.stage_decorator([dev])
    @bpp.run_decorator(md=_md)
    def _run_all():
        for cnt in range(repeat):
            yield from switch_feedback_one_step(dev, md = md, logger = logger)

    return (yield from _run_all())

def main():

    sw = SwitchFeedbackOnOff(name = 'sw')
    #print(sw.describe())
    install_qt_kicker()

    RE = RunEngine({})
    #RE.log.setLevel("DEBUG")
    RE.log.setLevel("INFO")


    bec = BestEffortCallback()
    RE.subscribe(bec)

    fig = plt.figure()
    ax = plt.gca()
    plots = [
        LivePlot('sw_feedback_x_active',          x = 'time', ax = ax),
        LivePlot('sw_feedback_z_active',          x = 'time', ax = ax),
        LivePlot('sw_topup_number_of_bunches',    x = 'time', ax = ax),
        LivePlot('sw_linac_gun_timer_gun_pulses', x = 'time', ax = ax),
    ]
    _md = {
        'target'   : 'study the effect of bunch on bunch feedback on injection efficiency',
        'operator' : ('Markus Ries', 'Pierre Schnizer')
    }
    runs = RE(switch_feedback(sw, 10 * 1000, logger = RE.log, md = _md), plots)

if __name__ == '__main__':
    plt.ion()
    main()
    plt.ioff()
    plt.show()
