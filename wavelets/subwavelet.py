#!/usr/bin/env python
# -*- coding: utf-8 -*-

class SkeletonToWavelet:
    def __init__(self, manager, wavelet_src, root_src):
        self.man = manager
        self.wavelet_src = wavelet_src
        self.root_src = root_src
        self.man.register_handler(root_src, self.handle_roots)
        self.man.add_data_id("subwavelet", "subwavelet", "wavelet")
    def handle_wavelet(self, ticket):
        self.wavelet = ticket.get_data().get_wavelet()
    def handle_roots(self, ticket):
        root = ticket.get_data()
        try:
            wavelet = ticket.find_parent_by_data_id(self.wavelet_src).get_data().get_wavelet()
            #print "Parsing root", ticket.description
            #print root.start_row(), root.start_offset()
            wv = self.root_to_subwavelet(wavelet, root)
            t = ticket.create_ticket("subwavelet", wv)
            self.man.push_ticket(t)
        except:
            print traceback.format_exc()
    def root_to_subwavelet(self, wavelet, root):
            start_index = root.relative_start_offset()-2
            stop_index = start_index+350
            wv = wavelet[:, start_index:stop_index]
            return wv

def init_module(manager, gui):
    return [SkeletonToWavelet(manager, "wavelet" ,"skeleton-root-valid")]

