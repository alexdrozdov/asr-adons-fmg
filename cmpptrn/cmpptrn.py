#!/usr/bin/env python
# -*- #coding: utf8 -*-

import copy
import manager
import localdb
import pickle

class CmpPtrnPlotter:
    def __init__(self):
        pass
    def add_pattern(self, pattern):
        pass

class CmpPtrnViewer:
    def __init__(self):
        pass
    def generate(self, ticket, plotter):
        ptrn = ticket.get_data()
        plotter.add_pattern(ptrn)

def init_module(manager, gui):
    localdb.db.write_temporary("/db/temporary/plotters/cmpptrn/class", CmpPtrnPlotter)
    localdb.db.write_temporary("/db/temporary/plotters/cmpptrn/name", "cmpptrn")
    localdb.db.write_temporary("/db/temporary/plotters/cmpptrn/caption", u"Привязка шаблонов к звукам")
    
    localdb.db.write_temporary("/db/temporary/viewers/cmpptrn-link/class", CmpPtrnViewer)
    localdb.db.write_temporary("/db/temporary/viewers/cmpptrn-link/id", "viewer-cmpptrn")
    localdb.db.write_temporary("/db/temporary/viewers/cmpptrn-link/caption", u"Привязка шаблонов к звукам")
    localdb.db.write_temporary("/db/temporary/viewers/cmpptrn-link/tags", ["pattern"])
    localdb.db.write_temporary("/db/temporary/viewers/cmpptrn-link/data_names", [])
    localdb.db.write_temporary("/db/temporary/viewers/cmpptrn-link/plotter/name", "cmpptrn")
    localdb.db.write_temporary("/db/temporary/viewers/cmpptrn-link/plotter/multiplexable", True)
    return [SkeletonCompare(manager, "wavelet" ,"skeleton-root-valid")]
