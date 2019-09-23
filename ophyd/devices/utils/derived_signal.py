from ophyd import DerivedSignal


class DerivedSignalLinear( DerivedSignal ):
    '''Rescale a derived signal using linear gains

    Args:
        parent_attr:      the name of the signal in the parent 
                          from which to derive from.
        parent_gain_attr: the gain (or gains) to use to scale
                          the signal defined above

    
    It assumes that the parent contains a signal object with 
    name defined by `parent_attr`. This signal can return a
    scalar or an other object.

    Currently used for rescaling the BPM's. 
    
    Warning:
         The signal `derived_from` can return 

    Todo:
        Check vector length and raise an appropriate Exception
        if these do not match
    '''
    def __init__(self, parent_attr, *, parent = None, parent_gain_attr = None,
                 parent_offset_attr = None, parent_bit_gain_attr = None,
                 **kwargs):
        bin_signal = getattr(parent, parent_attr)
        super().__init__(derived_from = bin_signal, parent = parent, **kwargs)

        if parent_gain_attr is None:
            self._gain = 1.0
        else:
            self._gain =  getattr(parent, parent_gain_attr)

        if parent_offset_attr is None:
            self._offset = 0.0
        else:
            self._offset = getattr(parent, parent_offset_attr)

        if parent_bit_gain_attr is None:
            self._bit_gain = 1.0
        else:
            self._bit_gain = getattr(parent, parent_bit_gain_attr)
    

    def getGain(self):
        gain = self._gain.value
        bit_gain = self._bit_gain.value
        gain  = gain * bit_gain
        return gain
    
    def forward(self, values):
        raise AssertionError('Not implemnted')
        return values * self._gain.value

    def inverse(self, values):
        gain = self.getGain()
        try:
            scaled = values / gain
        except Exception:
            fmt = 'value shape {} gain shape {}'
            self.log.error(fmt.format(values.shape, gain.shape))

        offset = self._offset.value
        r = scaled #- offset
        return r
