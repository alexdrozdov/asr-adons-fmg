#!/usr/bin/python
# -*- #coding: utf8 -*-

import mgrid
import numpy

class SumSpectrums:
	def __init__(self, manager):
		self.man = manager
		sp0_name = "mic 0 0 spectrum from src 0"
		sp1_name = "mic 0 0 spectrum from src 1"
		self.man.register_handler(sp0_name, self.sp0_handler)
		self.man.register_handler(sp1_name, self.sp1_handler)
		self.man.register_handler("mic 0 0 spectrum", self.sp_handler)
		self.man.add_data_id("mic 0 0 sum spectrum", "mic 0 0 sum spectrum", "spectrum")

	def sp_handler(self, spectrum):
		sp = self.sp0.get_y() + self.sp1.get_y()
		ss = mgrid.SignalSpectrum(None, None, self.sp0.get_x(), sp, None)
		self.man.push_data("mic 0 0 sum spectrum", ss)

	def sp0_handler(self, spectrum):
		self.sp0 = spectrum

	def sp1_handler(self, spectrum):
		self.sp1 = spectrum

def list_adons():
	return ['SumSpectrums']

def load_adons(manager, l=None):
	adons = {}
	adons['sum_sp'] = SumSpectrums(manager)
