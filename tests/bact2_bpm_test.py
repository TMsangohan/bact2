import sys
import os
import numpy as np
import time

from cycler import cycler
import bluesky.callbacks.best_effort

# update these directories to where you cloned the packages or install them
sys.path.append('/home/tmerten/github-repos/')
# sys.path.append('/net/nfs/srv/MachinePhysics/MachineDevelopment/Mertens/github-repos/')

from bluesky.utils import install_qt_kicker
import bluesky.callbacks as bc
from bluesky import RunEngine
import bluesky.plans as bp
from bluesky.utils import ProgressBarManager

import databroker

from ophyd import sim

from bact2.ophyd.devices.raw.BPMWaveformDetector import BPMStorageRing
from bact2.ophyd.utils.preprocessors.CounterSink import CounterSink


def main():
	print(time.time())
	# Repeat the measurement 5 times
	n_meas = 5

	# The frequency range
	f0 = 10
	f1 = 14
	freq = np.linspace(f0, f1, 3)



	# bpm = BPMWaveformDetector(name = "bpm")
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
	RE.log.setLevel("INFO")
	RE.subscribe(bec)
	# install_qt_kicker()
 
	# RE.waiting_hook = ProgressBarManager()

	db = databroker.Broker.named('temp')
	db = databroker.Broker.named('mongo')
	RE.subscribe(db.insert)

	uids = RE(bp.scan_nd(det, sw_freq * repeat))
	print(uids)

	headers = db[uids]
	header = headers[0]
	print(header)

	header = db[-1]
	df = header.table()

	print(df.columns)

if __name__ == '__main__':
	main()
