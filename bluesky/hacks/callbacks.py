"""Liveplot hack to ignore matplotlib legend.set_draggable


"""
from bluesky.callbacks import LivePlot as BSLivePlot
class Proxy:
    def __init__(self, obj):
        self._obj = obj

    def __getattr__(self, name):
        return getattr(self._obj, name)

class LegendWrapper( Proxy ):
    def set_draggable(self, flag):
        """not existing in this version

        Todo:
            use logger
        """
        print("Ignoring request to set legend draggable to {}".format(flag))

class AxisWrapper( Proxy ):
    def legend(self, *args, **kwargs):
        meth = getattr(self._obj, "legend")
        r = meth(*args, **kwargs)
        w = LegendWrapper(r)
        return w

class LivePlot( BSLivePlot ):
    """A hack to get Liveplot running with old matplotlib
    """
    def __init__(self, *args, ax = None, **kwargs):
        if ax is None:
            import matplotlib.pyplot as plt

            ax = plt.subplot()
            ax = AxisWrapper(ax)

        super().__init__(*args, ax = ax, **kwargs)
