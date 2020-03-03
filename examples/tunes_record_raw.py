import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

import datetime

import bluesky.plans as bp
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky import RunEngine
from bluesky.utils import install_qt_kicker

from databroker import Broker

from bact2.ophyd.devices.raw.tunes import TuneSpectrumRaw
from bact2.bluesky.live_plot.line_index import PlotLineVsIndex

from bluesky.callbacks import LivePlot

import numpy as np
import pprint

class PlotSpectrum( LivePlot ):
    '''Plots the spectrum of the given variable
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.x_axis_scale = 1.0

        # Extract the name of the used detector
        y_name = self.y
        tmp = y_name.split('_')
        assert(tmp[-1]=='spec')
        tmp = '_'.join(tmp[:-1])
        self.used_detector = tmp
        

    def descriptor(self, doc):
        """Resolution and raw data

        Extract the resolution from the variables next to the units.
        Make appropriate label names
        """

        assert(self.used_detector is not None)
        used_det_name = self.used_detector
        
        res_name = used_det_name + '_resolution'
        spec_name = used_det_name + '_spec'

        data_keys = doc['data_keys']
        spec_dic = data_keys[spec_name] 
        y_unit = spec_dic['units']
        y_src = spec_dic['source']
        self.ax.set_ylabel(f'{y_src} [{y_unit}]')

        x_unit = data_keys[res_name]['units']
        self.ax.set_xlabel(f'{used_det_name} [{x_unit}]')
        
        config = doc['configuration']
        conf_keys = list(config.keys())
            
        try:
            if len(conf_keys) == 1:
                used_det = config[conf_keys[0]]
            else:
                used_det = config[used_det_name]
        except Exception:
            print(f'Failed to find {used_det_name} in config doc')
            print(f'Configuration doc {config}')
            raise
        
        resolution = used_det['data'][res_name]
        self.x_axis_scale = resolution
        
        return super().descriptor(doc)

    def update_caches(self, x, y):
        ind = np.arange(len(y))
        x_scale = self.x_axis_scale
        ind = ind * x_scale
        
        self.x_data = ind.tolist()
        self.y_data = y.tolist()


def main():

    tunes_spec = TuneSpectrumRaw(name='tunes_raw')
    # print(tunes_spec.ch1.describe_configuration())
    # print(tunes_spec.ch1.describe())
    # return

    RE = RunEngine({})
    db = Broker.named('light')
    RE.subscribe(db.insert)
    bec = BestEffortCallback()
    RE.subscribe(bec)

    install_qt_kicker()


    fig = plt.figure()
    ax = plt.subplot(111)
    plt_spec1 = PlotSpectrum('tunes_raw_ch1_spec', ax=ax)
    plt_spec2 = PlotSpectrum('tunes_raw_ch2_spec', ax=ax)
    plots  = [plt_spec1, plt_spec2]

    
    end_forecast = datetime.datetime(2020, 3, 3, 8)
    start = datetime.datetime.now()
    dt = end_forecast - start
    readings_per_second = (6082 - 5783) / 60
    n_readings = dt.total_seconds() * readings_per_second
    
    # Channel two is too slow....
    det = [tunes_spec]
    test = True
    if test:
        n_readings = 500
        n_readings = 5

    n_readings = int(n_readings)
    comment = '''Measurement executed in parallel to classical beam based alignment measurement. 
This measurement was executed  2. March 2020 starting at roughly 22:30 CEST. Target have full spectrum available.
Now with liveplot. '''
    
    md = {
        'target' : 'tunes_raw_data',
        'extra' : test,
        'forecast of end' : end_forecast,
        'comment' : comment
    }
    
    uids = RE(bp.count(det, n_readings), plots, **md)
    print(f'uids: {uids}')

if __name__ == '__main__':
    plt.ion()
    main()
    plt.ioff()
    plt.show()

