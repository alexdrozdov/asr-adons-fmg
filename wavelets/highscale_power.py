
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import traceback
import numpy
from iwavelet import *

class HightscalePower:
    filter_cfg = {
#        6 : 20,
#        7 : 16,
#        8 : 12,
        9 : 12,
        10 : 12,
        11 : 12
    }
    start_row = 9
    def __init__(self, manager, wavelet_src, wavelet_dst):
        self.man = manager
        self.wavelet_src = wavelet_src
        self.wavelet_dst = wavelet_dst
        self.man.register_handler(wavelet_src, self.handle_wavelet)
        self.man.add_data_id(wavelet_dst, "subwavelet", "wavelet")
    def handle_wavelet(self, ticket):
        wv = self.highscale_to_power(ticket)
    def highscale_to_power(self, ticket):
        wavelet = ticket.get_data()
        wv_data = wavelet.get_wavelet()
        data_width = ticket.find_ticket_by_sticky('data-width').get_sticky('data-width')
        wv = numpy.zeros(wv_data.shape)
        for r,window_width in HightscalePower.filter_cfg.items():
            wv[r,:] = self.row_to_power(wv_data[r,:], window_width, data_width)
        wv[0:HightscalePower.start_row,:] = wv_data[0:HightscalePower.start_row,:]
        wv = SignalWavelet(range(wv.shape[1]), wavelet.get_scale(), wv)
        t = ticket.create_ticket(self.wavelet_dst, wv)
        self.man.push_ticket(t)
        return wv
    def row_to_power(self, row, window_width, data_width):
        row[0:data_width-1] = row[1:data_width]-row[0:data_width-1]
        row = numpy.abs(row)
        r = numpy.zeros(row.shape)
        for i in range(window_width/2, len(row)-window_width/2):
            r[i] = numpy.sum(row[i-window_width/2:i+window_width/2])
        r[0:data_width] -= numpy.mean(r[0:data_width])
        r /= numpy.max(numpy.abs(r))
        r[data_width:] = 0
        return r


class HighscaleSpectrumFilt(object):
    start_row = 9
    def __init__(self, manager, wavelet_src, wavelet_dst):
        self.man = manager
        self.wavelet_src = wavelet_src
        self.wavelet_dst = wavelet_dst
        self.man.register_handler(wavelet_src, self.handle_wavelet)
        self.man.add_data_id(wavelet_dst, "subwavelet", "wavelet")
    def handle_wavelet(self, ticket):
        wv = self.highscale_spectrum_filt(ticket)
    def highscale_spectrum_filt(self, ticket):
        wavelet = ticket.get_data()
        wv_data = wavelet.get_wavelet()
        wv = numpy.array(wv_data)
        for r in range(HighscaleSpectrumFilt.start_row, 11):
            wv_row = wv[r,:]
            wv_spect = numpy.fft.fftshift(numpy.fft.fft(wv_row))
            wv_spect[0:256] = 0.0
            wv_spect[280:] = 0
            wv_row = numpy.fft.ifft(numpy.fft.fftshift(wv_spect))
            wv_row /= numpy.max(numpy.abs(wv_row))
            wv[r,:] = wv_row
        wv = SignalWavelet(range(wv.shape[1]), wavelet.get_scale(), wv)
        t = ticket.create_ticket(self.wavelet_dst, wv)
        self.man.push_ticket(t)


def init_module(manager, gui):
    return [HightscalePower(manager, "subwavelet" ,"subwavelet-highscale-power"),
            HighscaleSpectrumFilt(manager, "subwavelet", "subwavelet-hightscale-filt")]

