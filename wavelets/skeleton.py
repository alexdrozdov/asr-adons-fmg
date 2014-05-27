#!/usr/bin/python
# -*- coding: utf-8 -

import numpy
import copy
import traceback

class SkeletonRow:
    def __init__(self):
        pass
    def process_row(self, matrix, row, start_index):
        pass

class SkeletonTrack:
    def __init__(self, skeleton_root, row, description):
        self.offsets = []
        self.scales = []
        self.powers = []
        self.row = row
        self.description = description
        self.skeleton_root = skeleton_root
        self.skeleton_root.register_track(self)
        self.weight = 0.0
        self.variance = 0.0
        self.a = None
        self.b = None
    def duplicate(self):
        st = SkeletonTrack(self.skeleton_root, self.row, self.description)
        st.offsets = copy.deepcopy(self.offsets)
        st.scales = copy.deepcopy(self.scales)
        st.powers = copy.deepcopy(self.powers)
        st.weight = self.weight
        st.variance = self.variance
        return st
    def find_max_in_range(self,matrix, row, start_index, stop_index):
        #print row, start_index, stop_index
        nz = numpy.nonzero(matrix[1][row,start_index:stop_index])[0]+start_index
        return nz
    def process(self, matrix, row, index):
        self.offsets.append(index)
        self.scales.append(row)
        self.powers.append(matrix[1][row, index])
        self.weight += matrix[1][row, index]
        if row-self.row>2:
            return

        if len(self.offsets)<2:
            predict_width = 150.0
        else:
            predict_width = int(numpy.mean(numpy.array(self.offsets[1:])-self.offsets[0])*1.3)
        r1 = row+1
        i1 = index+5
        nz = self.find_max_in_range(matrix, r1, i1, i1+predict_width)
        if len(nz)>0 and r1<matrix[1].shape[0]-1:
            for n in nz:
                st = self.duplicate()
                st.process(matrix, r1, n)

    def estimate_line(self):
        if len(self.offsets) < 3:
            return
        offsets = numpy.array(self.offsets)
        scales = numpy.array(self.scales)
        n = len(self.offsets)
        yy = offsets[1:]-offsets[0]
        xx = scales[1:]-scales[0]
        kk = yy/xx
        weights = numpy.arange(1.0, 0.6, -0.4/len(kk))
        #print kk.shape, weights.shape
        self.k = numpy.mean(numpy.multiply(kk, weights))
        self.b = offsets[0]-scales[0]*self.k
    def evalute_inlinearity(self):
        err = 0
        self.inlinearity = 100000.0
        if len(self.offsets) < 3:
            return
        self.estimate_line()
        for i in range(1,len(self.offsets)):
            x = float(self.scales[i])
            y = float(self.offsets[i])
            line_y = self.k*x+self.b
            e = line_y-y
            if e>0:
                e *= 0.6**(x-self.scales[0])
            err += numpy.abs(e)
        self.inlinearity = err/float(len(self.offsets)-1) 
        return self.inlinearity
    def evalute_weight(self):
        weight_norm = numpy.sum(numpy.arange(1.0, 0.7, -0.3/len(self.offsets)))
        self.norm_weight = self.weight / weight_norm
    def estimate_length(self):
        pass
    def length(self):
        return len(self.offsets)
    def print_offsets(self):
        print "    ", self.offsets, self.weight, self.norm_weight, self.evalute_inlinearity()
    def add_offset(self, offset):
        for i in range(len(self.offsets)):
            self.offsets[i] += offset

class SkeletonRoot:
    def __init__(self, row, index,description):
        self.row = row
        self.index = index
        self.description = description
        self.tracks = []
    def duplicate(self):
        return copy.deepcopy(self)
    def process(self, matrix):
        st = SkeletonTrack(self,self.row, self.description)
        st.process(matrix, self.row, self.index)
        self.filter_power_variance()
        self.filter_by_length()
        self.filter_anchestors()
        self.estimate_length()
        self.snapshot = [matrix[0][:, self.index-30:self.index+400],matrix[1][:, self.index-30:self.index+400] ]
        #self.print_root()
    def register_track(self, track):
        self.tracks.append(track)
    def print_root(self):
        if len(self.tracks)<1:
            return
        print "SkeletonRoot ", self.description, "at row=", self.row, "index=", self.index
        for t in self.tracks:
            t.print_offsets()
    def filter_by_length(self):
        max_length = 0
        min_length = 1000
        for t in self.tracks:
            t.evalute_inlinearity()
            t.evalute_weight()
            l = t.length()
            if l>max_length:
                max_length = l
            if l<min_length:
                min_length = l
        selected_tracks = []
        for l in range(min_length,max_length+1):
            #print l
            min_inlinearity = 100000.0
            min_track = None
            for t in self.tracks:
                #print t.row, t.offsets[0]
                if t.length()!=l:
                    continue
                if t.inlinearity<min_inlinearity:
                    min_inlinearity = t.inlinearity
                    min_track = t
            if None != min_track:
                selected_tracks.append(min_track)
        self.tracks = selected_tracks
        
    def filter_power_variance(self):
        selected_tracks = []
        for t in self.tracks:
            if len(t.powers)<2:
                continue
            v1 = numpy.var(t.powers)
            v2 = numpy.var(t.powers[1:])
            #print "off=", t.offsets, "v1=", v1, "v2=", v2
            if v1/v2>2.0 and t.powers[0]<t.powers[1]:
                #print "removing for variance..."
                continue
            if t.powers[1]/t.powers[0]>2.0:
                #print "removing for power..."
                continue
            selected_tracks.append(t)
        self.tracks = selected_tracks
            
    def filter_anchestors(self):
        self.tracks.sort(cmp = self.compare_tracks)
        if len(self.tracks)>0:
            self.tracks = [self.tracks[-1],]
    def estimate_length(self):
        for t in self.tracks:
            t.estimate_length()
        
    def compare_tracks(self, t1, t2):
        len_bonus = (t1.length()-t2.length())*0.5 / float(t1.length()+t2.length())
        power_bonus = (t1.norm_weight - t2.norm_weight)*0.2 / (t1.norm_weight + t2.norm_weight)
        inlinearity_bonus = (t2.inlinearity - t1.inlinearity)*0.3 / (t2.inlinearity + t1.inlinearity)
        bonus = len_bonus + power_bonus + inlinearity_bonus
        if bonus > 0:
            return 1
        if bonus < 0:
            return -1
        return 0
    def is_valid(self):
        return len(self.tracks)>=1
    def start_row(self):
        return self.row
    def stop_row(self):
        return self.row + len(self.tracks[0].offsets)
    def start_offset(self):
        return self.tracks[0].offsets[0]
    def stop_offset(self):
        return self.tracks[0].offsets[-1]
    def offset_at_row(self, row):
        ind = self.tracks[0].scales.index(row)
        return self.tracks[0].offsets[ind]
    def add_offset(self, offset):
        for t in self.tracks:
            t.add_offset(offset)
        self.index += offset

class SkeletonExtractor:
    def __init__(self, manager, src_name, dst_name, dst_desc = None):
        self.man = manager
        if None == dst_desc:
            dst_desc = dst_name
        self.man = manager
        self.man.register_handler(src_name, self.handler_matrix)
        self.man.add_data_id(dst_name, dst_desc, "object")
        self.src_name = src_name
        self.dst_name = dst_name
        self.dst_desc = dst_desc
        
        self.trig_rows = [3,4]
        
    def handler_matrix(self, ticket):
        matrix = ticket.get_data()
        self.matrix = matrix
        mtx = matrix[1]
        for i in range(0, mtx.shape[1]):
            for r in self.trig_rows:
                if mtx[r, i] != 0:
                    sr = SkeletonRoot(r, i, ticket.description)
                    sr.process(matrix)
                    if sr.is_valid():
                        self.man.push_ticket(ticket.create_ticket(self.dst_name, sr))

class SkeletonPrinter:
    def __init__(self, manager, src_name):
        self.man = manager
        self.src_name = src_name
        self.man.register_handler(src_name, self.print_handler)
    def print_handler(self, ticket):
        sr = ticket.get_data()
        sr.print_root()

class TicketFlow:
        def __init__(self, id):
            self.id = id
            self.skeleton_roots = []
        def compare_roots(self, r1, r2):
            t1 = r1.tracks[0]
            t2 = r2.tracks[0]
            row_bonus = (r2.row-r1.row) * 0.2
            len_bonus = (t1.length()-t2.length())*0.3 / float(t1.length()+t2.length())
            power_bonus = (t1.norm_weight - t2.norm_weight)*0.8 / (t1.norm_weight + t2.norm_weight)
            inlinearity_bonus = (t2.inlinearity - t1.inlinearity)*0.1 / (t2.inlinearity + t1.inlinearity)
            k_bonus = (t2.k-t1.k) * 0.2 / (t1.k+t2.k)
            bonus = row_bonus+len_bonus + power_bonus + inlinearity_bonus + k_bonus
            #print "bonus=",bonus, "k_bonus=", k_bonus, "len_bonus=", len_bonus, "row_bonus=", row_bonus, "power_bonus=", power_bonus, "inlinearity_bonus=", inlinearity_bonus
            return bonus
        def process(self, sr):
            #print "processing", sr.print_root()
            valid_roots = []
            sr_start = sr.start_offset()
            invalidate_sr = False
            selected_roots = []
            for s in self.skeleton_roots:
                if s.stop_offset()<sr_start:
                    valid_roots.append(s) # Пришел трэк, который уже не пересекается с этим.
                    continue
                # Возник конфликт, сравниваем треки по их параметрам на предмет оценки правдоподобия
                sr_bonus = self.compare_roots(sr, s)
                if sr_bonus<0:
                    selected_roots.append(s)
                    #print "invalidating", sr.print_root()
                    invalidate_sr = True #Новый трэк можно отбросить. Он пересекается и имеет меньший вес
                else:
                    pass
                    #print "forgetting", s.print_root()
            self.skeleton_roots = selected_roots
            if not invalidate_sr:
                self.skeleton_roots.append(sr)
                #print "appending", sr.print_root()
            return valid_roots

class SkeletonOverlapFilter:
    def __init__(self, manager, src_name, dst_name, dst_desc = None):
        self.man = manager
        if None == dst_desc:
            dst_desc = dst_name
        self.man = manager
        self.man.register_handler(src_name, self.handler_sr)
        self.man.add_data_id(dst_name, dst_desc, "object")
        self.src_name = src_name
        self.dst_name = dst_name
        self.dst_desc = dst_desc
        self.ticket_flows = {}
        
    def create_ticket_flow(self, id):
        self.ticket_flows[id] = TicketFlow(id)
        
    def process_ticket_flow(self, ticket):
        sr = ticket.get_data()
        ticket_id = ticket.get_root_id()
        if not self.ticket_flows.has_key(ticket_id):
            self.create_ticket_flow(ticket_id)
        tf = self.ticket_flows[ticket_id]
        valid_roots = tf.process(sr)
        for vr in valid_roots:
             self.man.push_ticket(ticket.create_ticket(self.dst_name, vr))
        
    def handler_sr(self, ticket):
        self.process_ticket_flow(ticket)

class SkeletonSamplerate:
    def __init__(self, manager, src_name):
        self.man = manager
        self.man.register_handler(src_name, self.handle_roots)
        self.src_name = src_name
        self.mean_width = None
        self.prev_root = None
        self.prev_layer = None
        self.prev_offset = None
        self.delta_offsets = []

    def handle_roots(self, ticket):
        root = ticket.get_data()
        root_layer = root.start_row()
        if None == self.prev_root:
            self.prev_root = root
            self.prev_offset = root.start_offset()
            self.prev_layer = root_layer
            return
        if root_layer==self.prev_layer:
            #Текущий корень начинается с того же уровня, что и предыдущий. Можно просто рассчитать разницу
            delta_offset = root.start_offset()-self.prev_offset
        else:
            if root_layer>self.prev_layer:
                #Текущий корень начинается выше чем предыдущий, необходимо определить аналгоичное смещение в предыдущем
                delta_offset = root.start_offset() - self.prev_root.tracks[0].offsets[root_layer-self.prev_layer]
            else:
                #Текущий корень начинается ниже чем предыдущий
                delta_offset = root.tracks[0].offsets[self.prev_layer-root_layer] - self.prev_offset

        self.prev_offset = root.start_offset()
        self.prev_layer = root_layer
        if None != self.mean_width:
            if numpy.abs(self.mean_width-delta_offset)<self.mean_width*0.5:
                self.mean_width = self.mean_width*0.9+delta_offset*0.1
        else:
            self.mean_width = delta_offset
        self.prev_root = root
        print "MeanWidth:", self.mean_width, "Offset:", delta_offset


class SkeletonFindBits:
    def __init__(self, manager, src_name):
        self.man = manager
        self.man.register_handler(src_name, self.handle_roots)
        self.src_name = src_name

    def handle_roots(self, ticket):
        root = ticket.get_data()
        try:
            n = 0
            print "Parsing root", ticket.description
            for r in range(root.start_row(), root.stop_row()):
                off = root.tracks[0].offsets[n]
                extr = numpy.nonzero(root.snapshot[1][r,:])[0]
                min_off = off-root.tracks[0].offsets[0]+30
                extr = extr[numpy.nonzero((extr-min_off+1.0)>0)]
                print "   ", r, min_off, extr, extr[1:]-extr[0:-1], root.snapshot[1][r, extr]
                n += 1
        except:
            print traceback.format_exc()

def init_module(manager, gui):
    return [SkeletonExtractor(manager, "wavelet-extremums-powers", "skeleton-root"),
            #SkeletonPrinter(manager, "skeleton-root")]
            SkeletonOverlapFilter(manager, "skeleton-root-merged", "skeleton-root-valid")]
            #SkeletonPrinter(manager, "skeleton-root-valid"),
            #SkeletonSamplerate(manager, "skeleton-root-valid"),
            #SkeletonFindBits(manager, "skeleton-root-valid")]
