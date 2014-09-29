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
                print traceback.format_exc()
            t = ticket.create_ticket("subwavelet", wv)
            self.man.push_ticket(t)
        except:
            print traceback.format_exc()
    def root_to_subwavelet(self, wavelet, root_ticket):
        skeleton_root = root_ticket.get_data()
        mean_width = int(root_ticket.find_ticket_by_sticky("mean-width").get_sticky("mean-width"))
        wavelet_data = wavelet.get_wavelet()
        subwavelet = numpy.zeros((wavelet_data.shape[0], 512))
        for r in range(12):
            r_offset = skeleton_root.relative_offset_at_row(r)
            subwavelet[r, 0:mean_width] = wavelet_data[r, r_offset:r_offset+mean_width]
        wv = SignalWavelet(range(mean_width), wavelet.get_scale(), subwavelet)
        return wv

def init_module(manager, gui):
    return [SkeletonToWavelet(manager, "wavelet" ,"skeleton-offsets")]

