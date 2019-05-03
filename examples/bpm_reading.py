from cycler import cycler

import bluesky.plans as bp
import bluesky.callbacks as bc
import bluesky.callbacks.best_effort
from bluesky import RunEngine
from bluesky.utils import ProgressBarManager
from bluesky.utils import install_qt_kicker

from ophyd import sim

import sys
sys.path.append('/home/tmerten/github-repos/')
# sys.path.append('/net/nfs/srv/MachinePhysics/MachineDevelopment/Mertens/github-repos/')
sys.path.append('/home/tmerten/gitlab-repos-hzb/suitcase-elasticsearch/')

# from suitcase.elasticsearch import Serializer

from bact2.ophyd.utils.preprocessors.CounterSink import CounterSink
from bact2.ophyd.devices.pp.bpm import BPMStorageRing
import numpy as np



def main():
    # Repeat the measurement 5 times
    n_meas = 20

    # The frequency range
    f0 = 10
    f1 = 14
    freq = np.linspace(f0, f1, 3)


    bpm = BPMStorageRing(name = "bpm")
    cs = CounterSink(name = "count_bpm_reads", delay = .0)
    cs = sim.motor2

    # cs.inform_set_done = bpm.waveform.new_trigger
    repeat = cycler(cs, range(n_meas))

    sw_freq = cycler(sim.motor, freq)


    if not bpm.connected:
        bpm.wait_for_connection()

    #print (bpm.trigger())
    #print (bpm.waveform.ready.read())
    det = [bpm]

    bec = bc.best_effort.BestEffortCallback()

    RE = RunEngine({})
    # RE.log.setLevel("INFO")
    #print(dir(bpm))
    bpm.waveform.validated_data.setLogger(RE.log)
    bpm.waveform.measurement_state.setLogger(RE.log)

    RE.subscribe(bec)
    install_qt_kicker()
    RE.waiting_hook = ProgressBarManager()

    # serializer = Serializer('localhost',9200)
    # RE.subscribe(serializer)

    RE(bp.scan_nd(det, sw_freq * repeat))


if __name__ == '__main__':
	main()
