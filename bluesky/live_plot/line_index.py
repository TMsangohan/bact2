"""Plot all data versus index

These plots update on every new data the whole line
"""

# from bact2.bluesky.hacks.callbacks import LivePlot
from bluesky.callbacks import LivePlot
import numpy as np

class PlotLineVsIndex( LivePlot ):
    """plot data versus index
    """
    def update_caches(self, x, y):
        ind = np.arange(len(y))
        self.x_data = ind.tolist()
        self.y_data = y.tolist()

class PlotLineVsIndexOffset( PlotLineVsIndex ):
    """Plot offset data  versus index

    The first measurement received is used as reference
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clearOffset()

    def clearOffset(self):
        self.old_value = None

    def update_caches(self, x, y):
        # Scale to kHz
        if self.old_value is None:
            self.old_value = y
        dy = y - self.old_value
        super().update_caches(x, dy)
