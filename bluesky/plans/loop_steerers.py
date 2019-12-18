"""looping over steerers


"""
from bluesky import plan_stubs as bps, preprocessors as bpp
import numpy as np
import logging
logger = logging.getLogger('bact2')



# Currents cycle ... respect hysteresis
current_signs = np.array([0, 1, -1, 0])

def step_steerer(steerer, currents, detectors, num_readings):
    """

    Todo:

    """
    # Using setpoint as reference ... assuming that this is the more
    # accurate value
    # make sure data are here
    yield from bps.trigger(steerer.setpoint)
    current_offset = steerer.setpoint.get()
    logger.info('Using steerer offset {:.5f}'.format(current_offset))

    for d_current in currents:
        t_current = d_current + current_offset
        logger.info('Setting steerer to I = {:.5f} = {:.5f} + {:.5f}'.format(t_current, current_offset, d_current))
        yield from bps.mv(steerer.setpoint, t_current)

        # Let's check if the first reading of the bpm is really useful
        # I guess first reading is too fast!
        # So first let's clear the offset plots
        # This is now handled by the BPM plot itself ...

        det = [steerer] + detectors
        for i in range(num_readings):
            yield from bps.trigger_and_read(det)
            # bps.read(detectors)



def select_step_steerer(col, name, currents, *args, **kws):
    '''Testing if run doc has to be issued
    '''

    logger.info('Selecting steerer {}'.format(name))
    yield from bps.mv(col, name)
    t_steerer = col.sel.dev
    # t_steerer = getattr(col.steerers, name)

    md_currents = currents
    md = kws.pop('md', {})
    md.update({'steerer_name' : name,
               'currents': md_currents})
    def _run():
        yield from step_steerer(t_steerer, currents, *args, **kws)

    return (yield from _run())

def loop_steerers(detectors, col, num_readings = 1, md = None,
                  horizontal_steerer_names = None, vertical_steerer_names = None,
                  current_val_horizontal = None, current_val_vertical = None,
                  current_steps = None,
                  **kws):
    """

    Warning:
          If the user defines current_steps, it is the users
          responsibility to ensure that these close

    Todo:
         Consider current steps, current vals etc best to be
         generators
    """
    # col_info = [col.selected.name, col.sel.name]
    # col_info = [col.selected.name]

    if current_steps is None:
        current_steps = current_signs
    else:
        current_steps = np.asarray(current_steps)

    _md = {'detectors': [det.name for det in detectors],
          'num_readings': num_readings,
          'plan_args': {
              'detectors': list(map(repr, detectors)),
              'num_readings': num_readings,
              'horizontal_steerer_names' : horizontal_steerer_names,
              'vertical_steerer_names'   : vertical_steerer_names,
              'current_val_horizontal'   : current_val_horizontal,
              'current_val_vertical'     : current_val_vertical,
              'current_steps'            : current_steps,
          },
          'plan_name': 'response_matrix',
          'hints': {}
    }
    _md.update(md or {})


    assert(horizontal_steerer_names is not None)
    assert(vertical_steerer_names   is not None)

    assert(current_val_horizontal is not None)
    assert(current_val_vertical   is not None)

    logger.info('Starting run_all')

    detectors_all = detectors + [col.selected]
    @bpp.stage_decorator(list(detectors) + [col])
    @bpp.run_decorator(md=md)
    def _run_all():
        """Iterate over vertical and horizontal steerers

        Get
        """
        # Lets do first the horizontal steerers and afterwards
        # lets get all vertial steerers

        currents = current_val_horizontal * current_steps
        for name in horizontal_steerer_names:
            logger.info('Selecting steerer {}'.format(name))
            yield from select_step_steerer(col, name, currents, detectors_all, num_readings, **kws)

        currents = current_val_vertical * current_steps
        for name in vertical_steerer_names:
            logger.info('Selecting steerer {}'.format(name))
            yield from select_step_steerer(col, name, currents, detectors_all, num_readings, **kws)


    return (yield from _run_all())
