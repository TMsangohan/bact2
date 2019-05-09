from ophyd import Device
from ophyd.status import DeviceStatus
from ophyd import Component as Cpt 
from ophyd import EpicsSignalRO, EpicsSignal
from ophyd import Signal

from cycler import cycler
import bluesky.callbacks.best_effort

from bluesky import RunEngine

import bluesky.plans as bp

from bluesky.utils import install_nb_kicker
import bluesky.callbacks as bc

from bluesky.callbacks import LiveTable

class BPMAccumulatingSignal( Device ):
    """
    Device class for measuring a fixed number of BPM wavefroms when triggered.
    
    Parameters are hardcoded as this only an example.
    """
    # the connection to the real data
    target = Cpt(EpicsSignal,"MDIZ2T5G:bdata")
    
    # constant
    window_size = Cpt(Signal, value=5)
    
    # last read value
    last_read = Cpt(Signal, value=[])
    
    def trigger(self):
        """
        Overwriting the parent class ( Device ) trigger method.
        """
        dbuffer = []
        count = 0
        target_N = self.window_size.get()
        
        # Create a status device 
        status = DeviceStatus(self)

        def accumulating_callback(value, **kwargs):
            """
            Define custom callback to subscribe to.
            """
            if status.done:
                self.target.clear_sub(accumulating_callback)
            nonlocal count

            dbuffer.append(value)
            count += 1

            if count >= target_N:
                self.last_read.put(dbuffer[:target_N])
                self.target.clear_sub(accumulating_callback)                        
                status._finished()

        self.target.subscribe(accumulating_callback, run=False)         

        return status

def main():
	bpm = BPMAccumulatingSignal(name="bpm_waveform")

	if not bpm.connected:
	    bpm.wait_for_connection()
	det = [bpm]

	bec = bc.best_effort.BestEffortCallback()

	RE = RunEngine({})

	RE.subscribe(bec)
	install_nb_kicker()

	def collect(naem, doc):
	    for el in doc['data']['bpm_waveform_last_read']:
	        print(el[:3])

	RE(bp.count(det),{'event':collect})

if __name__ == '__main__':
	main()