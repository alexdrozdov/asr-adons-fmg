#!/usr/bin/env python
# -*- coding: utf-8 -*-
import traceback
import numpy
from iwavelet import *

class SkeletonToWavelet:
    def __init__(self, manager, wavelet_src, root_src):
        self.man = manager
        self.wavelet_src = wavelet_src
        self.root_src = root_src
        self.man.register_handler(root_src, self.handle_roots)
        self.man.add_data_id("subwavelet", "subwavelet", "wavelet")
    def handle_roots(self, ticket):
        try:
            wavelet = ticket.find_parent_by_data_id(self.wavelet_src).get_data()
            try:
                wv = self.root_to_subwavelet(wavelet, ticket)
            except:
                return
            t = ticket.create_ticket("subwavelet", wv)
            self.man.push_ticket(t)
        except:
            print traceback.format_exc()
    def root_to_subwavelet(self, wavelet, root_ticket):
        skeleton_root = root_ticket.get_data()
        mean_width = int(root_ticket.find_ticket_by_sticky("mean-width").get_sticky("mean-width"))
        start_index = skeleton_root.relative_start_offset()-2
        stop_index = start_index+mean_width
        wavelet_data = wavelet.get_wavelet()
        subwavelet = numpy.zeros((wavelet_data.shape[0], 512))
        offset = skeleton_root.relative_start_offset()
        subwavelet[:, 0:mean_width+60] = wavelet_data[:, offset-60:offset+mean_width]
        wv = SignalWavelet(range(mean_width), wavelet.get_scale(), subwavelet)
        return wv

def init_module(manager, gui):
    return [SkeletonToWavelet(manager, "wavelet" ,"skeleton-root-valid")]

