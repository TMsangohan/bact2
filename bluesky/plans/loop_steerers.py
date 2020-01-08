"""looping over steerers


"""
from bluesky import plan_stubs as bps, preprocessors as bpp
from bluesky.utils import separate_devices, Msg

import numpy as np
import logging
logger = logging.getLogger('bact2')

import copy

# Currents cycle ... respect hysteresis
current_signs = np.array([0, 1, -1, 0])




from bact2.bluesky.live_plot.line_index import Offset

class OrbitTrace:
    def __init__(self):
        self._x_orbit = Offset()
        self._y_orbit = Offset()

    def clearOffset(self):
        self._x_orbit.clearOffset()
        self._y_orbit.clearOffset()

    def __call__(self, x, y):
        skip, dx = self._x_orbit.update_caches(None, x)
        skip, dy = self._y_orbit.update_caches(None, y)
        return dx, dy


def extract_bpm_data(val, bpm_prefix = 'bpm_waveform'):
    x_pos_name = '_'.join([bpm_prefix, 'x_pos'])
    y_pos_name = '_'.join([bpm_prefix, 'y_pos'])

    # for d in
    keys = val.keys()

    bpm_x =  val[x_pos_name]
    bpm_y =  val[y_pos_name]

    keys = bpm_x.keys()

    bpm_x_data = bpm_x['value']
    bpm_y_data = bpm_y['value']

    return bpm_x_data, bpm_y_data

orbit = OrbitTrace()

def calculate_orbit_offset(val, bpm_prefix = 'bpm_waveform'):
    bpm_x, bpm_y = extract_bpm_data(val)

    bpm_x = np.asarray(bpm_x)
    bpm_y = np.asarray(bpm_y)
    dx, dy = orbit(bpm_x, bpm_y)
    dr = np.sqrt(dx**2 + dy**2)

    fmt =  'Maximum orbit offset: x {:.3f}..{:.3f} y {:.3f}..{:.3f} dr {:.3f}'
    tup = dx.min(), dx.max(), dy.min(), dy.max(), dr.max()
    txt = fmt.format(*tup)
    # print(txt)
    return dr

def steerer_current_offset(steerer):
    # Using setpoint as reference ... assuming that this is the more
    # accurate value
    # make sure data are here
    yield from bps.trigger(steerer.setpoint)
    current_offset = steerer.setpoint.get()
    logger.info('Using steerer offset {:.5f}'.format(current_offset))
    return current_offset


def step_steerer(steerer, currents, detectors, num_readings, current_offset = None,
                 book_keeping_dev = None):
    """

    Todo:

    """

    assert(book_keeping_dev is not None)
    # Using setpoint as reference ... assuming that this is the more
    # accurate value
    # make sure data are here
    if current_offset is None:
        current_offset = (yield from steerer_current_offset(steerer))


    logger.info('Using steerer offset {:.5f}'.format(current_offset))

    for d_current in currents:
        if d_current == 0:
            #print('Current step 0')
            pass
        book_keeping_dev.dI.value = float(d_current)

        t_current = d_current + current_offset
        logger.info('Setting steerer to I = {:.5f} = {:.5f} + {:.5f}'.format(t_current, current_offset, d_current))
        yield from bps.mv(steerer.setpoint, t_current)

        # Let's check if the first reading of the bpm is really useful
        # I guess first reading is too fast!
        # So first let's clear the offset plots
        # This is now handled by the BPM plot itself ...

        det = [steerer] + detectors
        for i in range(num_readings):
            val = (yield from bps.trigger_and_read(det))
            # First bpm reading has to be ignored .....
            if i  > 0:
                # What a hack. I use it here so that the orbit
                # reference data get set
                calculate_orbit_offset(val)



def steerer_search_step(steerer, start_current, detectors, num_readings, bpm_prefix = 'bpm_waveform', dr_target = 1.0,
                        dr_scale_max = 25, dr_eps = 1e-2, eps_rel=.1, eps_clip = 1e-4,
                        current_offset  = None,
                        book_keeping_dev = None):
    """

    Todo:
       Fix: detectors should not change during run I guess
    """



    det = [steerer] + detectors

    d_current = 0

    d_current = start_current
    last_scale = 1

    assert(current_offset is not None)

    assert(dr_scale_max > 0)
    assert(eps_rel > 0)
    assert(dr_eps > 0)

    value_clipped = False

    limits = None
    limits = steerer.setpoint.limits
    print(steerer)
    print(steerer.setpoint)
    assert((np.absolute(limits)>1e-8).all())
    dl = limits[1] - limits[0]
    assert(dl>1e-8)

    total_scale = 1.0
    for i in range(5):
        t_current_test = d_current + current_offset

        assert(limits is not None)
        # if limits is not None:
        t_current = np.clip(t_current_test, *limits)
        d_current = t_current - current_offset

        book_keeping_dev.dI.value = float(d_current)

        txt = (
            f'Setting steerer to I = {t_current:.5f} =' +
            f' {current_offset:.5f} + {d_current:.5f} requested {t_current_test:.5f}'
        )
        logger.info(txt)

        diff = t_current_test - t_current
        adiff = np.absolute(diff)

        if adiff > eps_clip:
            value_clipped = True
            total_scale = (d_current / start_current)
            total_scale = total_scale * .9
            d_current = d_current *.9
            txt = (
                f'Steerer {steerer.name} requested current {t_current_test:.5f}'
                f' clipped to {t_current:.5f} diff {diff:e}'
                f' d_current {d_current:.5f} total scale {total_scale:.3f}'
            )
            logger.warning(txt)
            print(txt)
            break
        yield from bps.mv(steerer.setpoint, t_current)

        # Let's check if the first reading of the bpm is really useful
        # I guess first reading is too fast!


        assert(num_readings > 1)

        for i in range(num_readings):
            val = ( yield from bps.trigger_and_read(det) )

        dr = calculate_orbit_offset(val)
        dr_max = dr.max()
        print('Step found maximum offset {:.3f} mm for a current step of {:.3f}'.format(dr_max, d_current))

        if dr_max < dr_eps:
            print('Step found maximum offset {:.3f} mm < dr_eps {:.3f} no scaling'.format(dr_max, dr_eps))
            yield from bps.null()
            return None

        dr_scale = dr_target / dr_max
        d_current = d_current * dr_scale

        print('Testing scaling current by {:.3f} current step {:.3f}'.format(dr_scale, d_current))
        # Stop if change is less than 10 %
        dr_band = np.absolute(dr_scale) - 1
        dra = abs(dr_band)
        eps_rel = .1
        if dra < eps_rel:
            # Todo:
            #    Improve it to respect hysteresis loop
            #    e.g.
            fmt = 'Last scaling step only changed by {:.3f} < {:.3f} (total scaling factor {:.3f})'
            txt = fmt.format(dr_scale, eps_rel, total_scale)
            logger.info(txt)
            break

        total_scale = (d_current / start_current)
        book_keeping_dev.scale_factor.value = total_scale
        if np.absolute(total_scale) > dr_scale_max:
            d_current = dr_scale_max * start_current
            fmt = 'Limiting current scaling to {:.3f} (scaling factor {:.3f} requested): making current step {:.3f}'
            txt = fmt.format(dr_scale_max, total_scale, d_current)
            # This line is essential!
            total_scale = dr_scale_max
            print(txt)
            break


    return d_current, total_scale

def select_step_steerer(col, name, currents, *args, dr_target = 1.0,  book_keeping_dev = None, **kws):
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

    kws['book_keeping_dev'] = book_keeping_dev



    def _run():

        assert(book_keeping_dev is not None)

        book_keeping_dev.mode.value = 'current_offset'
        book_keeping_dev.current_offset.value = -1.0
        book_keeping_dev.scale_factor.value = -1.0
        book_keeping_dev.dI.value = 0.0
        book_keeping_dev.steerer_name.value = 'unknown'

        current_offset = (yield from steerer_current_offset(t_steerer))
        book_keeping_dev.current_offset.value = float(current_offset)

        # That should store the current orbit....
        book_keeping_dev.mode.value = 'reference_orbit'



        def _run_inner():

            yield from bps.checkpoint()
            #: thats important otherwise we move arond as each steps
            #: further down this plan builds on previous history

            orbit.clearOffset()
            yield from step_steerer(t_steerer, [0], *args,  current_offset = current_offset, **kws)

            # Find the maximum requested step
            scaled_currents = copy.copy(currents)
            currents_max = scaled_currents.max()

            # See if it requires to be scaled to some real offset
            val = None
            book_keeping_dev.mode.value = 'searching_scale'

            val = (yield from steerer_search_step(t_steerer, currents_max, *args, current_offset=current_offset, dr_target=dr_target, **kws))

            if val is not None:
                current_step, total_scale = val
                total_scale = abs(total_scale)
                if total_scale > 30:
                    total_scale = 30.0
                scaled_currents = currents * total_scale
                book_keeping_dev.scale_factor.value = float(total_scale)

            # run the hyseresis loop. I assume that I am on the branch upwards
            # That's something the power converter should know how to perform
            total_current = scaled_currents + current_offset

            c_max, c_min = total_current.max(), total_current.min()
            n_loops = 3
            steps = [c_max, c_min] * n_loops + [current_offset]
            hysteresis_currents = np.array(steps, np.float_)

            book_keeping_dev.mode.value = 'hysteresis_loop'
            for cur in hysteresis_currents:
                yield from bps.mv(t_steerer.setpoint, cur)

            book_keeping_dev.mode.value = 'store_data'
            # Take the data over all the requested currents
            yield from step_steerer(t_steerer, scaled_currents[0:], *args,  current_offset = current_offset, **kws)

        try:
            r = (yield from _run_inner())
        finally:
            book_keeping_dev.steerer_name.value = 'restore_data'
            # Should be there but if everything goes wrong ...
            # should be outside this function
            yield from bps.mv(t_steerer.setpoint, current_offset)


    return (yield from _run())

def loop_steerers(detectors, col, num_readings = 1, md = None,
                  horizontal_steerer_names = None, vertical_steerer_names = None,
                  current_val_horizontal = None, current_val_vertical = None,
                  current_steps = None,
                  book_keeping_dev = None,
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
              'keywords'                 : kws,
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

    detectors_all = (detectors
                     + [col.selected]
                     +  [book_keeping_dev]
    )
    @bpp.stage_decorator(detectors_all)
    @bpp.run_decorator(md=_md)
    def _run_all():
        """Iterate over vertical and horizontal steerers

        Get
        """
        # Lets do first the horizontal steerers and afterwards
        # lets get all vertial steerers

        # Define reference orbit but ignore first bpm reading

        orbit.clearOffset()

        kws['book_keeping_dev'] = book_keeping_dev

        currents = current_val_vertical * current_steps
        for name in vertical_steerer_names:
            logger.info('Selecting steerer {}'.format(name))
            yield from select_step_steerer(col, name, currents, detectors_all, num_readings, **kws)

        currents = current_val_horizontal * current_steps
        for name in horizontal_steerer_names:
            logger.info('Selecting steerer {}'.format(name))
            yield from select_step_steerer(col, name, currents, detectors_all, num_readings, **kws)



    return (yield from _run_all())
