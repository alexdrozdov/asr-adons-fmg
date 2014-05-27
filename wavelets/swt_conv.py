#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python
# -*- coding: utf-8 -*-

import sys
import getopt
import scipy.signal
import pickle
from exceptions import ValueError

def import_analize_modules():
    global numpy
    numpy      = __import__("numpy")
    global pywt
    pywt       = __import__("pywt")
    global math
    math       = __import__("math")


class SignalWavelet:
    def __init__(self, time, scale, wavelet, tag = None):
        self.time  = time
        self.scale  = scale
        self.wavelet = wavelet
        self.tag  = tag
    def get_time(self):
        return self.time
    def get_scale(self):
        return self.scale
    def get_wavelet(self):
        return self.wavelet

class SwtTransform:
    def __init__(self,manager):
        self.man = manager
        self.man.register_handler("swt config", self.handler_config)
        self.man.register_handler("wav", self.handler_run)
        self.man.add_data_id("wavelet", u"Результат вейвлет преобразования", "wavelet")

    def handler_config(self, ticket):
        config = ticket.get_data()
        self._family = config["family"]
        self._max_level = config["max_level"]
        self._wavelet = pywt.Wavelet(self._family)

    def handler_run(self, ticket):
        self.transform(ticket)
    
    def transform(self, ticket):
        signal = ticket.get_data().copy()
        original_len = signal.length()
        factor2_len  = int(2**math.ceil(math.log(original_len,2)))
        signal.extend(factor2_len)
        max_level = pywt.swt_max_level(factor2_len)
        if max_level and self._max_level>max_level:
            self._max_level = max_level
        wvl = pywt.swt(signal._sound, self._wavelet, max_level)
        wavelet = self.list2matrix(wvl, original_len)
        scales = numpy.array(range(max_level))
        times = numpy.array(range(factor2_len))
        w = SignalWavelet(times, scales, wavelet)
        self.man.push_ticket(ticket.create_ticket("wavelet", w))
        
    def wavelet_length(self):
        return self._swt_matrix.shape[1]
    
    def wavelet_range(self, rng):
        return self._swt_matrix[:,rng[0]:rng[1]]
        
    def list2matrix(self, wvl, original_len):
        m = len(wvl)
        n = min(wvl[0][1].shape[0],original_len)
        swt_matrix = numpy.zeros((m,n))
        for r_cnt in range(m):
            for c_cnt in range(n):
                swt_matrix[r_cnt,c_cnt] = wvl[r_cnt][1][c_cnt]
        return swt_matrix
                
    def swt_resize(self,new_size, multiline_resize = False):
        if multiline_resize:
            x_scale = new_size[1]/self._swt_matrix.shape[1]
            y_scale = new_size[0]/self._swt_matrix.shape[0]
            tmp_sig = numpy.repeat(self._swt_matrix, x_scale, axis=1)
            tmp_sig = numpy.repeat(tmp_sig, y_scale, axis=0)
        else:
            tmp_sig = scipy.signal.resample(self._swt_matrix,new_size[0], axis=0)
            tmp_sig = scipy.signal.resample(tmp_sig,new_size[1], axis=1)
        return tmp_sig
        
    def swt_range_scale(self,swt_mtx,range = None):
        max_val = numpy.max(numpy.max(swt_mtx))
        min_val = numpy.min(numpy.min(swt_mtx))
        swt_mtx_norm = (swt_mtx-min_val) / (max_val-min_val)
        if not range:
            range = (0,1)
        swt_mtx_exc = numpy.copy(swt_mtx_norm)
        swt_mtx_exc[swt_mtx_norm < range[0]] = range[0]
        swt_mtx_exc[swt_mtx_norm > range[1]] = range[1]
        
        max_val = numpy.max(numpy.max(swt_mtx_exc))
        min_val = numpy.min(numpy.min(swt_mtx_exc))
        return (swt_mtx_exc-min_val) / (max_val-min_val)

class ExtremumFinder:
    def __init__(self,manager, src_name, dst_min_max_name, dst_min_max_value_name, dst_min_max_power_name, dst_desc = None):
        if None == dst_desc:
            dst_desc = dst_min_max_name
        self.man = manager
        self.man.register_handler(src_name, self.handler_wavelet)
        self.man.add_data_id(dst_min_max_name, dst_desc, "matrix")
        self.man.add_data_id(dst_min_max_value_name, dst_desc, "matrix")
        self.man.add_data_id(dst_min_max_power_name, dst_desc, "matrix")
        self.src_name = src_name
        self.dst_min_max_name = dst_min_max_name
        self.dst_min_max_value_name = dst_min_max_value_name
        self.dst_min_max_power_name = dst_min_max_power_name
        self.dst_desc = dst_desc

    def handler_wavelet(self, ticket):
        wv = ticket.get_data()
        sig = wv.get_wavelet()
        sz = sig.shape
        tmp_min = numpy.zeros(sz)
        tmp_max = numpy.zeros(sz)
        
        # Посик максимумов и минимумов. По координатам макимумов и минимумов записываются "1"
        sig_h1 = numpy.hstack((numpy.zeros((sz[0],1)), sig[:,0:sz[1]-1]))
        sig_h2 = numpy.hstack((numpy.zeros((sz[0],2)), sig[:,0:sz[1]-2]))
        sig_h3 = numpy.hstack((sig[:,1:sz[1]], numpy.zeros((sz[0],1))))
        sig_h4 = numpy.hstack((sig[:,2:sz[1]], numpy.zeros((sz[0],2))))
        positive_h1 = numpy.int32((sig - sig_h1)>0)
        positive_h2 = numpy.int32((sig - sig_h2)>0)
        positive_h3 = numpy.int32((sig - sig_h3)>0)
        positive_h4 = numpy.int32((sig - sig_h4)>0)
        max_h = numpy.int32((positive_h1 + positive_h2 + positive_h3 + positive_h4)==4)
        negative_h1 = numpy.int32((sig - sig_h1)<0)
        negative_h2 = numpy.int32((sig - sig_h2)<0)
        negative_h3 = numpy.int32((sig - sig_h3)<0)
        negative_h4 = numpy.int32((sig - sig_h4)<0)
        min_h = numpy.int32((negative_h1 + negative_h2 + negative_h3 + negative_h4)==4)

        self.man.push_ticket(ticket.create_ticket(self.dst_min_max_name, (min_h, max_h)))
        
        # Подстановка значений максимумов и минимумов всесто "1"
        max_h_value = numpy.multiply(numpy.int32(max_h!=0), sig)
        min_h_value = numpy.multiply(numpy.int32(min_h!=0), sig)
        self.man.push_ticket(ticket.create_ticket(self.dst_min_max_value_name, (min_h_value, max_h_value)))
        
        # Подстановка сумарного значения в окрестности максимума или минимума
        max_h_power = numpy.zeros(max_h.shape)
        for r in range(max_h.shape[0]):
            if r>7:
                break
            trig_min = False
            left_min_coord = 0
            max_coord = 0
            trig_max = False
            for c in range(max_h.shape[1]):
                if min_h[r,c]>0:
                    if not trig_max:
                        trig_min = True
                        left_min_coord = c
                    else:
                        trig_min = True
                        trig_max = False
                        right_min_coord = c
                        vals = sig[r, int((left_min_coord+max_coord)/2):int((max_coord+c)/2)]
                        vals = numpy.multiply(vals, vals*sig[r,max_coord]>0)
                        v = numpy.sum(vals)
                        if v>0:
                            max_h_power[r,max_coord] = numpy.log(v)
                        left_min_coord = c
                if max_h[r,c] and trig_min:
                    trig_max = True
                    max_coord = c
        min_h_power = numpy.zeros(min_h.shape)
        for r in range(min_h.shape[0]):
            if r>7:
                break
            trig_max = False
            left_max_coord = 0
            min_coord = 0
            trig_min = False
            for c in range(min_h.shape[1]):
                if max_h[r,c]>0:
                    if not trig_min:
                        trig_max = True
                        left_max_coord = c
                    else:
                        trig_max = True
                        trig_min = False
                        right_max_coord = c
                        vals = sig[r, int((left_max_coord+min_coord)/2):int((min_coord+c)/2)]
                        vals = numpy.multiply(vals, vals*sig[r,min_coord]>0)
                        v = numpy.sum(vals)
                        if v>0:
                            min_h_power[r,min_coord] = numpy.log(v)
                        left_max_coord = c
                if min_h[r,c] and trig_max:
                    trig_min = True
                    min_coord = c
        self.man.push_ticket(ticket.create_ticket(self.dst_min_max_power_name, (min_h_power, max_h_power)))

class ExtremumToWavelet:
    def __init__(self, manager, src_name, dst_name, dst_desc = None):
        if None == dst_desc:
            dst_desc = dst_name
        self.man = manager
        self.man.register_handler(src_name, self.handler_matrix)
        self.man.add_data_id(dst_name, dst_desc, "wavelet")
        self.src_name = src_name
        self.dst_name = dst_name
        self.dst_desc = dst_desc

    def handler_matrix(self, ticket):
        mtx = ticket.get_data()
        wv = mtx[0]*(-1.0) + mtx[1]
        wv[:,1:-4] += wv[:, 2:-3] + wv[:, 0:-5] + wv[:, 3:-2] + wv[:, 4:-1]
        w = SignalWavelet(None, None, wv)
        self.man.push_ticket(ticket.create_ticket(self.dst_name, w))

class WaveletReshaper:
    def __init__(self,manager, src_name, dst_name, dst_desc = None):
        if None == dst_desc:
            dst_desc = dst_name
        self.man = manager
        self.man.register_handler("swt config", self.handler_config)
        self.man.register_handler(src_name, self.handler_wavelet)
        self.man.add_data_id(dst_name, dst_desc, "wavelet")
        self.src_name = src_name
        self.dst_name = dst_name
        self.dst_desc = dst_desc

    def handler_config(self, ticket):
        config = ticket.get_data()
        self._reshape_method = config["reshape-method"]
        self._reshape_size = config["reshape-size"]
        self._vflip = config["reshape-vflip"]

    def handler_wavelet(self, ticket):
        wv = ticket.get_data()
        if self._reshape_method=="multiline_resize":
            if self._reshape_size[1] >= 0:
                x_scale = self._reshape_size[1]/wv.get_wavelet().shape[1]
                if x_scale >= 1:
                    tmp_sig = numpy.repeat(wv.get_wavelet(), x_scale, axis=1)
                else:
                    new_x_line = numpy.array(numpy.arange(0, wv.get_wavelet().shape[1]-1, float(wv.get_wavelet().shape[1]-1)/float(self._reshape_size[1])), int)
                    tmp_sig = wv.get_wavelet()[:,new_x_line]
            else:
                tmp_sig = wv.get_wavelet()
            y_scale = self._reshape_size[0]/wv.get_wavelet().shape[0]
            tmp_sig = numpy.repeat(tmp_sig, y_scale, axis=0)
        else:
            tmp_sig = scipy.signal.resample(wv.get_wavelet(),self._reshape_size[0], axis=0)
            tmp_sig = scipy.signal.resample(tmp_sig,self._reshape_size[1], axis=1)
        if self._vflip:
            tmp_sig = numpy.flipud(tmp_sig)
        w = SignalWavelet(wv.get_time(), wv.get_scale(), tmp_sig)
        self.man.push_ticket(ticket.create_ticket(self.dst_name, w))


def init_module(manager, gui):
    import_analize_modules()
    return [SwtTransform(manager),
        WaveletReshaper(manager, "wavelet", "wavelet-reshaped"),
        ExtremumFinder(manager , "wavelet", "wavelet-extremums", "wavelet-extremums-values", "wavelet-extremums-powers"),
        ExtremumToWavelet(manager, "wavelet-extremums", "wavelet-extremums-wv"),
        WaveletReshaper(manager, "wavelet-extremums-wv", "wavelet-extremums-wv-rh"),
        ExtremumToWavelet(manager, "wavelet-extremums-powers", "wavelet-extremums-powers-wv"),
        WaveletReshaper(manager, "wavelet-extremums-powers-wv", "wavelet-extremums-powers-wv-rh")]



