'''Plots for comparing the different bpm data

'''
from collections import ChainMap
from bluesky.callbacks import LivePlot
import numpy as np

class BPMComparisonPlot( LivePlot ):
    '''

    Todo:
        Investigate is such a plot should be provided for steerers too
    '''
    def __init__(self, *args, bpm_names = None, bpm_positions = None, **kwargs):

        assert(bpm_names is not None)
        assert(bpm_positions is not None)

        super().__init__(*args, **kwargs)

        self._bpm_names = list(bpm_names)
        self._bpm_positions = bpm_positions
        self._bpm_names = np.array(self._bpm_names, dtype='U20')

        self.x_data = None
        self.y_data = None

    def start(self, doc):
        # The doc is not used; we just use the signal that a new run began.
        self._epoch_offset = doc['time']  # used if self.x == 'time'

        self.x_data = self._bpm_positions
        self.y_data = np.zeros(len(self.x_data), np.float_)
        self.y_data[:] = np.nan

        label = " :: ".join(
            [str(doc.get(name, name)) for name in self.legend_keys])
        kwargs = ChainMap(self.kwargs, {'label': label})

        self.current_line, = self.ax.plot(self.x_data, self.y_data, **kwargs)
        # self.current_line, = self.ax.plot([], [], **kwargs)
        self.lines.append(self.current_line)

        legend = self.ax.legend(loc=0, title=self.legend_title)
        try:
            # matplotlib v3.x
            self.legend = legend.set_draggable(True)
        except AttributeError:
            # matplotlib v2.x (warns in 3.x)
            self.legend = legend.draggable(True)

        self.setBPMNamesAsXTicks()

    def setBPMNamesAsXTicks(self):
        self.ax.set_xticks(self._bpm_positions)
        self.ax.set_xticklabels(self._bpm_names, fontsize = 'small',
                                verticalalignment = 'top', horizontalalignment='center')
        for tick in self.ax.get_xticklabels():
            tick.set_rotation(90)

    def update_caches(self, x, y):
        '''
        '''

        lx_d = len(self.x_data)
        assert(lx_d > 0)

        ly = len(y)
        if ly != lx_d:
            fmt = 'Length did not match for len(y) = {} len(self.x_data) = {}'
            raise AssertionError(fmt.format(ly, lx_d))

        self.y_data = y

    def update_plot(self):
        self.current_line.set_data(self.x_data, self.y_data)

        self.ax.relim(visible_only=True)
        self.ax.autoscale_view(tight=True)

        axis = list(self.ax.axis())
        x_data = np.array(self.x_data)
        axis[0] = x_data.min()
        axis[1] = x_data.max()
        self.ax.axis(axis)
        self.ax.figure.canvas.draw_idle()


    def stop(self, doc):
        '''

        Todo:
            Check if stop method can be reworked
        '''
        self.x_data = list(self.x_data)
        self.y_data = list(self.y_data)
        super().stop(doc)
