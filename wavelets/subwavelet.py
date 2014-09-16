#!/usr/bin/env python
# -*- coding: utf-8 -*-
import traceback
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
            wv = self.root_to_subwavelet(wavelet, ticket)
            t = ticket.create_ticket("subwavelet", wv)
            self.man.push_ticket(t)
        except:
            print traceback.format_exc()
    def root_to_subwavelet(self, wavelet, root_ticket):
        skeleton_root = root_ticket.get_data()
        mean_width = int(root_ticket.get_sticky("mean-width"))
        start_index = skeleton_root.relative_start_offset()-2
        stop_index = start_index+mean_width
        wavelet_data = wavelet.get_wavelet()
        wv = SignalWavelet(range(mean_width), wavelet.get_scale(), wavelet_data[:, start_index:stop_index])
        return wv

def init_module(manager, gui):
    return [SkeletonToWavelet(manager, "wavelet" ,"skeleton-root-valid")]

