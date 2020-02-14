from ocelot.cpbd.magnetic_lattice import MagneticLattice
from ocelot.cpbd.optics import twiss, Navigator, MethodTM, TransferMap, SecondTM
from ocelot.cpbd.orbit_correction import NewOrbit, lattice_track
from ocelot.cpbd.response_matrix import RingRM, ResponseMatrix
from ocelot.cpbd.track  import track
from ocelot.cpbd.match  import closed_orbit
from ocelot.cpbd.beam import ParticleArray, Particle, Beam, Twiss

import collections
import functools
import numpy as np
import sys

from dataclasses import dataclass
import copy

# from ocelot.gui.accelerator import plot_opt_func, plot_API


bessy_ii_path = '/home/mfp/Devel/bessy_ii/'

if bessy_ii_path not in sys.path:
    sys.path.append(bessy_ii_path)
import bessy_updated


@dataclass
class OrbitData:
    x: np.ndarray
    y: np.ndarray
    s: np.ndarray


@dataclass
class OrbitBpmTrace:
    bpm: OrbitData
    trace: OrbitData


class OrbitCalculator:
    def __init__(self, cell=bessy_updated.cell):

        method = MethodTM()

        # Trying to avoid side effects
        cell = copy.deepcopy(cell)
        lat = MagneticLattice(cell, method=method)

        orb = NewOrbit(lat)

        method = RingRM(lattice=orb.lat,
                        hcors=orb.hcors, vcors=orb.vcors,
                        bpms=orb.bpms)
        orb.response_matrix = ResponseMatrix(method=method)
        orb.response_matrix.calculate()

        orb.correction(beta=500, epsilon_x=1e-9, epsilon_y=1e-9,
                       print_log=False)

        self.cell = cell
        self.orb = orb
        self.method = method
        self.lat_od = collections.OrderedDict()

        # Lookup for the element
        seq = self.orb.lat.sequence
        for cnt in range(len(seq)):
            elem = seq[cnt]
            name = elem.id
            self.lat_od[name] = cnt

    @functools.lru_cache(maxsize=2)
    def getBPMDs(self):
        return np.array([p.s for p in self.orb.bpms])

    def _orbitData(self, write2bpms=False):
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
        # bpm = {'s': ds_bpm_b, 'x': x_bpm_b, 'y': y_bpm_b}
        bpm = OrbitData(x=x_bpm_b, y=y_bpm_b, s=ds_bpm_b)

        # d = collections.OrderedDict()
        # d['bpm'] = bpm

        pl = lattice_track(self.orb.lat, self.method.particle0)
        dtypes = np.dtype({'names': ['s', 'x', 'y'], 'formats': [np.float_]*3})
        pla = np.array([(p.s, p.x, p.y) for p in pl], dtypes)
        # d['trace'] = pla
        trace = OrbitData(x=pla['x'], y=pla['y'], s=pla['s'])

        d = OrbitBpmTrace(bpm=bpm, trace=trace)

        return d

    def storeReferenceOrbit(self):
        return self._orbitData(write2bpms=True)

    def _orbitForChangedMagnet(self):
        self.orb.lat.update_transfer_maps()
        return self._orbitData()

    def getElementbyName(self, name):
        assert(name is not None)
        num = self.lat_od[name]
        element = self.orb.lat.sequence[num]
        if element is None:
            txt = (
                f'Could not find element named {name}'
                f' (tracked to sequence number {num})'
                )
            raise AssertionError(txt)
        assert(name == element.id)
        return element

    def orbitForChangedMagnet(self, name=None, angle=None):

        if name is None:
            return self._orbitData()

        element = self.getElementbyName(name)

        last_value = element.angle
        try:
            element.angle = angle
            r = self._orbitForChangedMagnet()
        finally:
            element.angle = last_value
            pass

        return r
