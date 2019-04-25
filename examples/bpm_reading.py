from cycler import cycler

import bluesky.plans as bp
import bluesky.callbacks as bc
import bluesky.callbacks.best_effort
from bluesky import RunEngine
from bluesky.utils import ProgressBarManager
from bluesky.utils import install_qt_kicker

from ophyd import sim

from bact2.ophyd.utils.preprocessors.CounterSink import CounterSink
from bact2.ophyd.devices.pp.bpm import BPMStorageRing
import numpy as np


def main():
	# Repeat the measurement 5 times
	n_meas = 5

	# The frequency range
	f0 = 10
	f1 = 14
	freq = np.linspace(f0, f1, 3)


	bpm = BPMStorageRing(name = "bpm")
	cs = CounterSink(name = "count_bpm_reads", delay = .0)

	cs.inform_set_done = bpm.waveform.new_trigger
	repeat = cycler(cs, range(n_meas))

	sw_freq = cycler(sim.motor, freq)


	if not bpm.connected:
	    bpm.wait_for_connection()

	det = [bpm]

	bec = bc.best_effort.BestEffortCallback()

	RE = RunEngine({})
	RE.log.setLevel("DEBUG")
	RE.subscribe(bec)
	install_qt_kicker()
	RE.waiting_hook = ProgressBarManager()


	RE(bp.scan_nd(det, sw_freq * repeat))


if __name__ == '__main__':
	main()
