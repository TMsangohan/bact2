'''

Todo:
   remove dependency on lattice of BESSY II
'''

from ocelot.cpbd.magnetic_lattice import MagneticLattice
from ocelot.cpbd.elements import Hcor, Vcor
from ocelot.cpbd.optics import twiss, Navigator, MethodTM, TransferMap, SecondTM
from ocelot.cpbd.orbit_correction import NewOrbit, lattice_track
from ocelot.cpbd.response_matrix import RingRM, ResponseMatrix
from ocelot.cpbd.track  import track
from ocelot.cpbd.match  import closed_orbit
from ocelot.cpbd.beam import ParticleArray, Particle, Beam, Twiss

import collections
import functools
import numpy as np
import os.path
import sys
import logging

from dataclasses import dataclass
import copy as _copy

# from ocelot.gui.accelerator import plot_opt_func, plot_API

bessy_ii_path = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__),
        *([os.path.pardir] * 4 + ['bessy_ii'])
    )
)

if bessy_ii_path not in sys.path:
    sys.path.append(bessy_ii_path)
import bessy_updated


log = logging.getLogger('bact2')

@dataclass
class OrbitData:
    x: np.ndarray
    y: np.ndarray
    s: np.ndarray


@dataclass
class OrbitBpmTrace:
    bpm: OrbitData
    trace: OrbitData

cell = bessy_updated.cell

# Inject fake steerers for modelling
ncell = []
for element in cell:
    ncell.append(element)
    fake_steerer = None

    if isinstance(element, Hcor):
        fake_id = element.id + '_artefact'
        fake_steerer = Vcor(l=0, angle=0, eid=fake_id)
    elif isinstance(element, Vcor):
        fake_id = element.id + '_artefact'
        fake_steerer = Hcor(l=0, angle=0, eid=fake_id)


    if fake_steerer:
        logging.debug(f'Adding fake steerer {fake_steerer}')
        ncell.append(fake_steerer)


class OrbitCalculator:
    def __init__(self, cell=cell, copy=True, init_lattice=True):

        # Trying to avoid side effects
        if copy:
            cell = _copy.deepcopy(cell)

        self.cell = cell
        self.orb = None
        self.method = None
        self.lat_od = None
        self.lat = None

        # Lookup for the element
        self.lat_od = collections.OrderedDict()
        seq = self.cell
        for cnt in range(len(seq)):
            elem = seq[cnt]
            name = elem.id
            self.lat_od[name] = cnt

        if init_lattice:
            self.initLattice()

    def initLattice(self):

        method = MethodTM()
        lat = MagneticLattice(self.cell, method=method)
        orb = NewOrbit(lat)

        method = RingRM(lattice=orb.lat,
                        hcors=orb.hcors, vcors=orb.vcors,
                        bpms=orb.bpms)
        orb.response_matrix = ResponseMatrix(method=method)
        orb.response_matrix.calculate()

        orb.correction(beta=500, epsilon_x=1e-9, epsilon_y=1e-9,
                       print_log=False)

        self.orb = orb
        self.method = method
        self.lat = lat

    @functools.lru_cache(maxsize=2)
    def getBPMDs(self):
        return np.array([p.s for p in self.orb.bpms])

    def orbitData(self, write2bpms=False):
        '''

        if name is None and value is None the reference orbit will
        be returned
        '''

        # I am not sure if it is a good idea to write to the b
        # beam position monitors
        # assert(write2bpms == False)

        rvo = self.method.read_virtual_orbit
        x_bpm_b, y_bpm_b = rvo(p_init=None, write2bpms=write2bpms)
        ds_bpm_b = self.getBPMDs()
        bpm = OrbitData(x=x_bpm_b, y=y_bpm_b, s=ds_bpm_b)

        pl = lattice_track(self.orb.lat, self.method.particle0)
        dtypes = np.dtype({'names': ['s', 'x', 'y'], 'formats': [np.float_]*3})
        pla = np.array([(p.s, p.x, p.y) for p in pl], dtypes)
        trace = OrbitData(x=pla['x'], y=pla['y'], s=pla['s'])

        d = OrbitBpmTrace(bpm=bpm, trace=trace)

        return d

    def twissParameters(self):
        assert(self.lat is not None)
        tws = twiss(self.lat, tws0=None)
        return tws

    def twissParametersBpms(self):
        bpm_ids = [p.id for p in self.orb.bpms]
        twiss = self.twissParameters()

        r = []
        for tws in twiss:
            if tws.id in bpm_ids:
                r.append(tws)
        return r

    def storeReferenceOrbit(self):
        return self._orbitData(write2bpms=True)

    def _orbitForChangedMagnet(self):
        self.orb.lat.update_transfer_maps()
        return self._orbitData()

    def getElementNumberByName(self, name):
        assert(name is not None)
        num = self.lat_od[name]
        return num

    def getElementbyName(self, name):

        num = self.getElementNumberByName(name)

        element = self.cell[num]
        if element is None:
            txt = (
                f'Could not find element named {name}'
                f' (tracked to sequence number {num})'
                )
            raise AssertionError(txt)
        assert(name == element.id)
        return element

    # def orbitForChangedMagnet(self, name=None, angle=None):
    #
    #     if name is None:
    #         return self._orbitData()
    #
    #     element = self.getElementbyName(name)
    #
    #     last_value = element.angle
    #     try:
    #         element.angle = angle
    #         r = self._orbitForChangedMagnet()
    #     finally:
    #         element.angle = last_value
    #         pass
    #
    #     return r

    def orbitCalculatorWithNewElement(self, name=None, init_lattice=True):
        '''

        Returns: neworbit, ne_element

        '''
        assert(name is not None)

        element = self.getElementbyName(name)
        new_element = _copy.deepcopy(element)

        num = self.getElementNumberByName(name)
        new_cell = _copy.copy(self.cell)
        new_cell[num] = new_element

        ins = self.__class__(new_cell, copy=False, init_lattice=init_lattice)
        return new_element, ins

    def orbitCalculatorForChangedQuadrupole(self, name=None, rk1=None,
                                            dx=None, dy=None, init_lattice=True):
        '''
        '''
        from ocelot.cpbd.elements import XYQuadrupole

        if rk1 is not None:
            rk1 = float(rk1)
            drk1 = abs(rk1)
            # Debug purpose: do not allow a quadrupole change by more than 10 %
            max_scale = .1
            if drk1 > max_scale:
                txt = (
                    f'Requested relative scale'
                    f' for k1 {rk1} is more than {max_scale}.'
                    f' Interal parameters drk1 {drk1}'
                )
                raise AssertionError(txt)

            assert(abs(drk1) < .1)

        r = self.orbitCalculatorWithNewElement(name, init_lattice=False)
        new_element, new_orbit = r

        if rk1 is not None:
            # Apply k for quadruole
            k1 = new_element.k1
            nk1 = k1 * (1 + rk1)
            new_element.k1 = nk1

        # Apply offset
        assert(isinstance(new_element, XYQuadrupole))

        if dx is not None:
            dx = float(dx)
            new_element.dx = dx
            new_element.x_offs = dx

        if dy is not None:
            dy = float(dy)
            new_element.dy = dy
            new_element.y_offs = dy

        log.info(f'Created new lattice with relative k1 change {rk1} dx {dx} dy  {dy}')
        if init_lattice:
            new_orbit.initLattice()
        return new_orbit

    def orbitCalculatorForChangedMagnet(self, name=None, angle=None,
                                        init_lattice=True):
        '''
        '''
        angle = float(angle)

        r = self.orbitCalculatorWithNewElement(name, init_lattice=False)
        new_element, new_orbit = r
        new_element.angle = angle
        if init_lattice:
            new_orbit.initLattice()
        return new_orbit


class _OrbitCalcOffset:
    def __init__(self):
        self._reference_data = None

    @property
    def reference_data(self):
        assert(self._reference_data is not None)
        return self._reference_data

    @reference_data.setter
    def reference_data(self, ref):
        self._reference_data = None
        self.checkAttributes(ref)
        self._reference_data = ref

    def checkAttributes(self, ref):
        txt = 'Do not use this class. Use derived class instead'
        raise NotImplementedError(txt)


class OrbitDataOffset(_OrbitCalcOffset):
    def checkAttributes(self, ref):
        '''Check that attributes which are required for further calculation exists
        '''
        ref.x
        ref.y
        ref.s

    def diff(self, arg1, arg2):

        orbit_data = arg1
        ref = arg2

        dx = orbit_data.x - ref.x
        dy = orbit_data.y - ref.y

        ds_check = orbit_data.s - ref.s
        check = np.absolute(ds_check)
        # Should be defined by machine precision.
        # I think thats a resonable value
        _eps = 1e-10
        cm = check.max()
        if cm >= _eps:
            txt = f'maxium deviation in ds {cm} > eps {_eps}'
            log.error(txt)
            # raise AssertionError(txt)

        diff = OrbitData(x=dx, y=dy, s=ref.s)
        return diff

    def __call__(self, orbit_data):
        '''Calculates the difference

        Todo:
            Should one check the s vectors?
        '''
        ref = self.reference_data
        return self.diff(orbit_data, ref)


class OrbitOffset(_OrbitCalcOffset):

    def __init__(self):
        super().__init__()
        self._filter = OrbitDataOffset()

    def checkAttributes(self, ref):
        '''Check that attributes which are required for further calculation exists
        '''
        ref.bpm
        ref.trace

    def diff(self, arg1, arg2):

        orbit_data = arg1
        ref = arg2

        assert(orbit_data is not None)
        assert(ref is not None)

        diff_func = self._filter.diff
        diff_bpm = diff_func(orbit_data.bpm, ref.bpm)
        diff_trace = diff_func(orbit_data.trace, ref.trace)

        r = OrbitBpmTrace(bpm=diff_bpm, trace=diff_trace)
        return r

    def __call__(self, orbit):
        '''Calculates the difference

        '''
        ref = self.reference_data
        r = self.diff(orbit, ref)
        return r
