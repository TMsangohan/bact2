"""looping over steerers


"""
from bluesky import plan_stubs as bps, preprocessors as bpp
import numpy as np
import logging
logger = logging.getLogger('bact2')



# Currents cycle ... respect hysteresis
current_signs = np.array([0, 1, -1, 0])

def step_steerer(steerer, currents, detectors, num_readings,
                 bpm_x_o = None, bpm_y_o = None):
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
        [p.clearOffset() for p in (bpm_x_o, bpm_y_o) if p is not None]
        for i in range(num_readings):
            yield from bps.trigger_and_read(detectors)

def loop_steerers(detectors, col, num_readings = 1, md = None,
                  horizontal_steerer_names = None, vertical_steerer_names = None,
                  current_val_horizontal = None, current_val_vertical = None,
                  **kws
):
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


    assert(horizontal_steerer_names is not None)
    assert(vertical_steerer_names   is not None)

    assert(current_val_horizontal is not None)
    assert(current_val_vertical   is not None)

    logger.info('Starting run_all')

    @bpp.stage_decorator(list(detectors) + [col])
    @bpp.run_decorator(md=_md)
    def _run_all():
        """Iterate over vertical and horizontal steerers

        Get 
        """            
        # Lets do first the horizontal steerers and afterwards
        # lets get all vertial steerers

        currents = current_val_horizontal * current_signs

        for name in horizontal_steerer_names:
            logger.info('Selecting steerer {}'.format(name))
            yield from bps.mv(col, name)
            yield from step_steerer(col.sel.dev, currents, detectors, num_readings, **kws)

        currents = current_val_vertical * current_signs
        for name in vertical_steerer_names:
            logger.info('Selecting steerer {}'.format(name))
            yield from bps.mv(col, name)
            yield from step_steerer(col.sel.dev, currents, detectors, num_readings)


    return (yield from _run_all())

