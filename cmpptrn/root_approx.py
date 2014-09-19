#!/usr/bin/env python
# -*- #coding: utf8 -*-

import manager
import localdb
import pickle
import numpy
import numpy.linalg

class RootApprox(object):
    def __init__(self, manager, src_name):
        self.man = manager
        self.src_name = src_name
        self.man.register_handler(self.src_name, self.handle_root)
    def handle_root(self, ticket):
        root = ticket.get_data()
        rows = range(root.start_row(), root.stop_row())
        x = numpy.array(rows)
        y = numpy.array([root.relative_offset_at_row(r) for r in rows])
        print y
        aproximated_y = self.approx(x, y)
        print aproximated_y
    def _aprox_3_point(self, x,y):
        a_matrix=numpy.matrix([[x[0]**2,x[0],1],[x[1]**2,x[1],1],[x[2]**2,x[2],1]])
        b_vector = y.T
        r = numpy.linalg.solve(a_matrix, b_vector)
        return r
    def _estimate_error(self, x, y, r):
        y_new = numpy.array(  [  r[0]*(x**2)+r[1]*x+r[2] for x in x ] )
        #print "y_new",y_new
        #print "y", y
        return numpy.sum(numpy.abs(y_new-y))
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
        return numpy.array(  [  best_approx[0]*(x**2)+best_approx[1]*x+best_approx[2] for x in range(1,12) ] )

def init_module(manager, gui):
    ra = RootApprox(manager, "skeleton-root-valid")
    return [ra,]

