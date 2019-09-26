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
        '''

        Todo:
           The current method is not used and thus needs to be
           checked before usage
        '''
        raise NotImplementedError('Code requires to be checked')

        sval = values * self._gain.value
        r  = sval + self._offset.value
        return r

    def inverse(self, values):
        '''

        Todo:
           The current method is not used and thus needs to be
           checked before usage
        '''
        raise NotImplementedError('Code requires to be checked')

        gain = self.getGain()
        dval = values - self._offset.value
        r = dval / gain
        return r


class DerivedSignalLinearBPM( DerivedSignalLinear ):
    '''BPM raw data to signal

    The inverse is used for calculating the bpm offset
    in mm from the raw data.
    '''
    def forward(self, values):
        raise NotImplementedError('Can not make a bpm a steerer')

    def inverse(self, values):
        '''BPM raw to physics coordinates

        BPM data are first scaled from raw data to mm.
        Then the offset is subtracted.
        '''
        gain = self.getGain()
        try:
            scaled = values / gain
        except Exception:
            fmt = 'value shape {} gain shape {}'
            self.log.error(fmt.format(values.shape, gain.shape))

        offset = self._offset.value
        r = scaled - offset
        return r
