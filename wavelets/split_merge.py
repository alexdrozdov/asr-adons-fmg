#!/usr/bin/python
# -*- coding: utf-8 -

import numpy
import music

class SignalBuffer:
    def __init__(self, manager, ticket_id, buffer_len, overlap):
        self.man = manager
        self.ticket_id = ticket_id
        self.signal_buffer = None
        self.buffer_len = buffer_len
        self.overlap = overlap
        self.current_pos = 0
        
    def handle_wav(self, ticket):
        wav = ticket.get_data()
        if None == self.signal_buffer:
            self.signal_buffer = wav._sound
        else:
            self.signal_buffer = numpy.hstack((self.signal_buffer,wav._sound))
        #print self.signal_buffer.shape
        while len(self.signal_buffer)>=self.buffer_len:
            part_sig = self.signal_buffer[0:self.buffer_len]
            self.signal_buffer = self.signal_buffer[self.buffer_len-self.overlap:]
            ws = music.WavSound(wav.samplerate(), part_sig)
            t = ticket.create_ticket("wav", ws)
            split_info = {"absolute-pos"          : self.current_pos,
                           "absolute-window-left"  : self.current_pos+100,
                           "absolute-window-right" : self.current_pos+self.buffer_len-self.overlap+100,
                           "window-left"           : 100,
                           "window-right"          : self.buffer_len-self.overlap+100}
            t.add_sticky("split-info", split_info)
            self.man.push_ticket(t)
            self.current_pos += self.buffer_len-self.overlap
    
    def handle_root(self, ticket):
        info = ticket.find_ticket_by_sticky("split-info").get_sticky("split-info")
        skel_root = ticket.get_data()
        start_offset = skel_root.start_offset()
        if start_offset>=info["window-left"] and start_offset<info["window-right"]:
            skel_root = skel_root.duplicate()
            skel_root.add_offset(info["absolute-pos"])
            self.man.push_ticket(ticket.create_ticket("skeleton-root-merged", skel_root))
        else:
            print "Purging", ticket.get_full_id(), "as lying outside window", info["window-left"] , info["window-right"], "at", start_offset

class WavSplit:
    def __init__(self, manager, src_name, dst_name, dst_desc = None):
        self.man = manager
        if None == dst_desc:
            dst_desc = dst_name
        self.man = manager
        self.man.register_handler(src_name, self.handler_wav)
        self.man.register_handler("skeleton-root", self.handler_root)
        self.man.add_data_id(dst_name, dst_desc, "object")
        self.man.add_data_id("wav", "wav-sound", "wav-sound")
        self.src_name = src_name
        self.dst_name = dst_name
        self.dst_desc = dst_desc
        
        self.signal_buffers = {}
        
    def handler_wav(self, ticket):
        ticket_id = ticket.get_root_id()
        if not self.signal_buffers.has_key(ticket_id):
            self.signal_buffers[ticket_id] = SignalBuffer(self.man, ticket_id, 2660, 600)
        self.signal_buffers[ticket_id].handle_wav(ticket)
    def handler_root(self, ticket):
        ticket_id = ticket.get_root_id()
        if not self.signal_buffers.has_key(ticket_id):
            print "Ticket with unregistered root id"
            return
        self.signal_buffers[ticket_id].handle_root(ticket)
        
class WaveletMerge:
    pass

def init_module(manager, gui):
    return [WavSplit(manager, "run", "skeleton-root-merged", u"Узлы, привязанные к глобальному времени")]
    