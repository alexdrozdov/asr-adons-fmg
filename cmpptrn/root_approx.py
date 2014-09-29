#!/usr/bin/env python
# -*- #coding: utf8 -*-

import manager
import localdb
import pickle
import numpy
import numpy.linalg


class SkeletonOffset:
    def __init__(self, skeleton_root, approx_offsets):
        self.row = skeleton_root.row
        self.index = skeleton_root.index
        self.description = skeleton_root.description
        self.global_offset = skeleton_root.global_offset
        self.__stop_row = self.row + len(skeleton_root.tracks[0].offsets)
        self.track = approx_offsets
    def duplicate(self):
        return copy.deepcopy(self)
    def process(self, matrix):
        pass
    def register_track(self, track):
        pass
    def print_root(self):
        pass
    def filter_by_length(self):
        pass
    def filter_power_variance(self):
        pass
    def filter_anchestors(self):
        pass
    def estimate_length(self):
        pass
    def compare_tracks(self, t1, t2):
        pass
    def is_valid(self):
        return True
    def start_row(self):
        return self.row
    def stop_row(self):
        return self.__stop_row
    def start_offset(self):
        return self.track[self.row]
    def stop_offset(self):
        return self.track[self.stop_row()-1]
    def offset_at_row(self, row):
        return self.track[row]
    def add_offset(self, offset):
        self.track = [t+offset for t in self.track]
        self.index += offset
        self.global_offset += offset
    def relative_start_offset(self):
        return self.start_offset()- self.global_offset
    def relative_stop_offset(self):
        return self.stop_offset() - self.global_offset
    def relative_offset_at_row(self, row):
        return self.offset_at_row(row) - self.global_offset

class RootApprox(object):
    def __init__(self, manager, src_name, dst_name):
        self.man = manager
        self.src_name = src_name
        self.dst_name = dst_name
        self.man.register_handler(self.src_name, self.handle_root)
        self.man.add_data_id(self.dst_name, description=u"Аппроксимированные смещения фронта", tag="undefined")
    def handle_root(self, ticket):
        root = ticket.get_data()
        rows = range(root.start_row(), root.stop_row())
        x = numpy.array(rows)
        y = numpy.array([root.relative_offset_at_row(r) for r in rows])
        aproximated_y = self.approx(x, y)
        so = SkeletonOffset(root, aproximated_y)
        self.man.push_ticket(ticket.create_ticket(self.dst_name, so))
    def _aprox_3_point(self, x,y):
        a_matrix=numpy.matrix([[x[0]**2,x[0],1],[x[1]**2,x[1],1],[x[2]**2,x[2],1]])
        b_vector = y.T
        r = numpy.linalg.solve(a_matrix, b_vector)
        return r
    def _estimate_error(self, x, y, r):
        y_new = numpy.array(  [  r[0]*(x**2)+r[1]*x+r[2] for x in x ] )
        return numpy.sum(numpy.abs(y_new-y))
    def _approx(self, x, y, best_approx):
        new_y_dict = { i:best_approx[0]*(i**2)+best_approx[1]*i+best_approx[2] for i in range(0,12) }
        for i in range(len(x)):
            xx = x[i]
            yy = y[i]
            if new_y_dict[xx]>yy:
                new_y_dict[xx] = yy
        prev_new_y = new_y_dict[1]
        y = []
        for i in range(0,12):
            yy = new_y_dict[i]
            if yy<prev_new_y:
                yy = prev_new_y
            prev_new_y = yy
            y.append(int(yy))
        return y
    def approx(self, x,y):
        if len(x)<3:
            raise ValueError(u"Оптимизация предполагает наличие минимум трех отметок")
        variative_idxs = range(1,len(x)-1)
        min_err = 1e9
        best_approx = None
        for v_idx in variative_idxs:
            xx = numpy.array([ x[0], x[v_idx], x[len(x)-1] ])
            yy = numpy.array([ y[0], y[v_idx], y[len(x)-1] ])
            r = self._aprox_3_point(xx, yy)
            err = self._estimate_error(x, y, r)
            if err<min_err:
                best_approx = r
                min_err = err
        return self._approx(x, y, best_approx)
    
class RootOffsets(object):
    def __init__(self, manager, src_name, dst_name):
        self.__init_fixed_row_offsets()
        self.man = manager
        self.src_name = src_name
        self.dst_name = dst_name
        self.man.register_handler(self.src_name, self.handle_root)
        self.man.add_data_id(self.dst_name, description=u"Аппроксимированные смещения фронта", tag="undefined")
    def handle_root(self, ticket):
        root = ticket.get_data()
        offsets = {}
        for r in range(root.start_row(), root.stop_row()):
            offsets[r] = root.relative_offset_at_row(r) - self.fixed_row_offsets[r]
        for r in range(root.start_row()):
            offsets[r] = root.relative_start_offset() - self.fixed_row_offsets[r]
        for r in range(root.stop_row(), 12):
            offsets[r] = root.relative_stop_offset() - self.fixed_row_offsets[r]
        offsets = [offsets[r] for r in range(12)]
        so = SkeletonOffset(root, offsets)
        self.man.push_ticket(ticket.create_ticket(self.dst_name, so))
    def __init_fixed_row_offsets(self):
        self.fixed_row_offsets = {r:20 for r in range(12)}
        self.fixed_row_offsets[0] = 60
        self.fixed_row_offsets[1] = 60
        self.fixed_row_offsets[2] = 60
        self.fixed_row_offsets[3] = 60
        self.fixed_row_offsets[4] = 40


def init_module(manager, gui):
    ra = RootOffsets(manager, "skeleton-root-valid", "skeleton-offsets")
    return [ra,]

