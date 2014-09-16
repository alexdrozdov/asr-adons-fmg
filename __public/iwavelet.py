#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python
# -*- coding: utf-8 -*-

class SignalWavelet:
    def __init__(self, time, scale, wavelet, tag = None):
        self.time  = time
        self.scale  = scale
        self.wavelet = wavelet
        self.tag  = tag
    def get_time(self):
        return self.time
    def get_scale(self):
        return self.scale
    def get_wavelet(self):
        return self.wavelet
