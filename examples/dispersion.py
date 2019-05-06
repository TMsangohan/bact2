# append to sys path to have access to bact2 and elasticsearch suitcase
import sys
sys.path.append('/opt/OPI/MachinePhysics/MachineDevelopment/Schnizer/github/')
sys.path.append('/opt/OPI/MachinePhysics/MachineDevelopment/Mertens/github-repos/suitcase-elasticsearch/')

# standard package imports
import numpy as np
import elasticsearch
import pprint
from getpass import getpass
import pandas as pd
from cycler import cycler
from sshtunnel import SSHTunnelForwarder

# ophyd imports
from ophyd import sim

# bluesky imports
import bluesky.plans as bp
import bluesky.callbacks as bc
import bluesky.callbacks.best_effort
from bluesky import RunEngine
from bluesky.utils import ProgressBarManager
from bluesky.utils import install_qt_kicker

# bact2 imports
from bact2.ophyd.utils.preprocessors.CounterSink import CounterSink
from bact2.ophyd.devices.pp.bpm import BPMStorageRing
from bact2.ophyd.devices.raw.master_clock import MasterClock

# elasticsearch suitcase imports
from suitcase.elasticsearch import Serializer

def main():
	# SSH TUNNELING CODE (TEMP SOLUTION TO HAVE ACCESS TO ELASTICSEARCH)
	MONGO_HOST = "skylab.acc.bessy.de"
	MONGO_DB = "StorageRing"
	login = getpass()
	pwd = getpass()
	MONGO_USER = login
	MONGO_PASS = pwd

	server = SSHTunnelForwarder(
		  MONGO_HOST,
		  ssh_username=MONGO_USER,
		  ssh_password=MONGO_PASS,
		  remote_bind_address=('0.0.0.0', 9200)
	)

	# START SSH TUNNEL SERVER
	server.start()

	# set number of desired measurements per motor step
	n_meas = 5  #5


	# f_ref = 499626.63033
	f_ref = 499624.43033

	# set scan range for the masterclock
	f0 = f_ref - 1 
	f1 = f_ref + 1
	freq = np.linspace(f0, f1, 10) 

	# load bpm class
	bpm = BPMStorageRing(name = "bpm")

	# load masterclock class
	mc = MasterClock(name = "master_clock")

	# secondary motor for the n_meas
	cs = sim.motor2
	repeat = cycler(cs, range(n_meas))

	# motor for the freq scan
	sw_freq = cycler(mc.frequency, freq)

	if not bpm.connected:
		  bpm.wait_for_connection()

	det = [bpm]

	bec = bc.best_effort.BestEffortCallback()

	RE = RunEngine({})
	#RE.log.setLevel("DEBUG")
	mc.frequency.setLogger(RE.log)

	bpm.waveform.validated_data.setLogger(RE.log)
	bpm.waveform.measurement_state.setLogger(RE.log)

	RE.subscribe(bec)
	install_qt_kicker()
	RE.waiting_hook = ProgressBarManager()

  # RunEngine subscribe elasticsearch 
	serializer = Serializer('localhost',server.local_bind_port)
	RE.subscribe(serializer)

	# Run the measurement
	RE(bp.scan_nd(det, sw_freq * repeat))

	# STOP SSH TUNNER SERVER
	server.stop()
