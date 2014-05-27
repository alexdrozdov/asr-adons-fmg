#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy

class PatternItem:
	def __init__(self, sign, row, def_offset, left_delta, right_delta):
		self.sign = sign
		self.row = row
		self.def_offset = def_offset
		self.left_delta = left_delta
		self.right_delta = right_delta
		self.cfg = [row, def_offset, left_delta, right_delta]
		self.offsets = []
		self.offsets.append(self.def_offset)

class PatternDescription:
	def __init__(self, trig_row):
		self.trig_row = trig_row
		self.items = []
		self.pattern = []
	def add_item(self, item):
		self.items.append(item)
	def build_pattern(self):
		for i in self.items:
			self.pattern.append(i.cfg)
	def evalute_pattern(self, matrix, offset):
		v = 0;
		for i in self.items:
			mtx = matrix[0] if i.sign<0 else matrix[1]
			v += numpy.sum(mtx[i.row, offset+i.def_offset-i.left_delta:offset+i.def_offset+i.right_delta])
		return v

	def adapt_pattern(self, matrix, offset):
		for i in self.items:
			m = numpy.mean(numpy.nonzero(matrix[i.row, offset+i.def_offset-i.left_delta:offset+i.def_offset+i.right_delta]))
			if numpy.isnan(m):
				continue
			i.offsets.append(int(i.def_offset-i.left_delta+m))
			i.def_offset = int(numpy.mean(i.offsets))
	def print_pattern(self):
		for i in self.items:
			print "offset:", i.def_offset, "left:", i.left_delta, "right:", i.right_delta, "offsets:", i.offsets


class PatternMatch:
	def __init__(self, index):
		self.index = index
	def get_index(self):
		return self.index

class PatternFinder:
	def __init__(self, manager, src_name, dst_name, dst_desc = None):
		self.man = manager
		if None == dst_desc:
			dst_desc = dst_name
		self.man = manager
		self.man.register_handler(src_name, self.handler_matrix)
		self.man.register_handler("match", self.handler_match)
		self.man.add_data_id(dst_name, dst_desc, "matrix")
		self.src_name = src_name
		self.dst_name = dst_name
		self.dst_desc = dst_desc

		self.pd0 = PatternDescription(3)
		self.pd0.add_item(PatternItem(-1, 4, 129, 20, 20))
		self.pd0.add_item(PatternItem(-1, 5, 183, 10, 10))
		self.pd0.add_item(PatternItem(-1, 6, 230, 10, 10))
		self.pd0.add_item(PatternItem(-1, 7, 242, 10, 10))
		self.pd0.build_pattern()

		self.pd = {}
		self.pd["e"] = PatternDescription(None)
		self.pd["e"].add_item(PatternItem(-1, 5, 306, 10, 10))
		self.pd["e"].add_item(PatternItem(-1, 6, 327, 10, 10))
		self.pd["e"].add_item(PatternItem(-1, 7, 342, 10, 10))
		self.pd["e"].add_item(PatternItem(+1, 5, 584-334, 10, 10))
		self.pd["e"].add_item(PatternItem(+1, 6, 610-334, 10, 10))

		self.pd["i"] = PatternDescription(None)
		self.pd["i"].add_item(PatternItem(-1, 5, 396, 20, 20))
		self.pd["i"].add_item(PatternItem(+1, 3, 549-325, 10, 10))
		self.pd["i"].add_item(PatternItem(+1, 4, 587-325, 20, 20))
		self.pd["i"].add_item(PatternItem(+1, 5, 633-325, 20, 20))

		self.pd["o"] = PatternDescription(None)
		self.pd["o"].add_item(PatternItem(-1, 5, 306, 10, 10))
		self.pd["o"].add_item(PatternItem(-1, 6, 327, 10, 10))
		self.pd["o"].add_item(PatternItem(-1, 7, 342, 10, 10))
		self.pd["o"].add_item(PatternItem(+1, 5, 584-334, 10, 10))
		self.pd["o"].add_item(PatternItem(+1, 6, 610-334, 10, 10))
		self.pd["o"].add_item(PatternItem(+1, 6, 757-372, 10, 10))
		self.pd["o"].add_item(PatternItem(+1, 5, 721-372, 10, 10))
		self.pd["o"].add_item(PatternItem(-1, 6, 797-372, 10, 10))
		self.pd["o"].add_item(PatternItem(-1, 5, 775-372, 10, 10))


		self.last_match = 0

	def handler_matrix(self, ticket):
		matrix = ticket.get_data()
		self.matrix = matrix
		mtx = matrix[0]
		for i in range(0, mtx.shape[1]):
			if mtx[self.pd0.trig_row, i] != 0:
				v = self.pd0.evalute_pattern(matrix, i)
				if v > 2:
					print i, v
					self.pd0.adapt_pattern(mtx,i)
					#self.pd0.print_pattern()
					m = PatternMatch(i)
					self.man.add_data_id("match", "Совпадение", "match")
					self.man.push_ticket(ticket.create_ticket("match", m))
	
	def handler_match(self, ticket):
		m = ticket.get_data()
		ind = m.get_index()
		for k in self.pd.keys():
			v = self.pd[k].evalute_pattern(self.matrix, ind)
			if v>1:
				print k," detected at ", ind

def init_module(manager, gui):
    return []
   	#[PatternFinder(manager, "wavelet-extremums", "nonedata")]


