#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import math
import numpy
import pylab
import scipy, scipy.signal
from numpy.fft import *
from math import sin, cos, pi, sqrt
from exceptions import ValueError

class SignalCommon:
    def __init__(self):
        pass
    def get_x(self):
        pass
    def get_y(self):
        pass

class MicrophoneSignal(SignalCommon):
    def __init__(self, row, col, data, tag):
        self.row  = row
        self.col  = col
        self.data = data
        self.tag  = tag
    def get_x(self):
        return numpy.arange(len(self.data))
    def get_y(self):
        return self.data
        
        
class SignalSpectrum:
    def __init__(self, row, col, freq, data, tag):
        self.row  = row
        self.col  = col
        self.freq = freq
        self.data = data
        self.tag  = tag
    def get_x(self):
        return self.freq
    def get_y(self):
        return self.data
    
class DirCoord:
    def __init__(self, index, value, frequency, angle):
        self.index = index
        self.value = value
        self.frequency = frequency
        self.angle = angle

class DirCoords:
    def __init__(self, samplerate, signal_len, coords):
        self.samplerate = samplerate
        self.signal_len = signal_len
        self.coords = coords

class Microphone:
    def __init__(self, manager, row, col, x, y, samplerate, amplify):
        self.man = manager
        self.x = x
        self.y = y
        self.row = row
        self.col = col
        self.z = 0.0
        self.amplify = amplify
        self._last_distance = 0.0;
        self.samplerate = samplerate
        self.timedelay = 0.0
        self.dig_delay = 0
        self.result_name = "mic " + str(self.row) + " " + str(self.col) + " signal"
        self.man.dis.add_data_id(self.result_name,
                                u'Сигнал на выходе микрофона в позиции ' + str(self.row) + " " + str(self.col),
                                "signal")
        self.result_id = self.man.dis.get_data_id(self.result_name)
    
    def print_position(self):
        print self.x,",",self.y,"\t",
        
    def print_timedelay(self):
        print str(self.timedelay)+"("+str(self.dig_delay)+")\t",
        
    def distance_to(self, point):
        x = point[0]
        y = point[1]
        z = point[2]
        self._last_distance = sqrt((x-self.x)**2.0 +(y-self.y)**2.0 +(z-self.z)**2.0 )
        return self._last_distance
    
    def last_distance(self):
        return self._last_distance
    
    # Установка задержки, необходимой для выравнивания фазового фронта
    def set_time_delay(self, delay):
        self.timedelay = delay
        self.dig_delay = int(round(delay*self.samplerate))
        
    def get_time_delay(self):
        return self.timedelay
    
    def receive_from(self, ticket):
        source = ticket.get_data()
        oversampled_frq = source[0].samplerate #Частота дискретизации сигнала
        full_sig_len = int(source[0].length*self.samplerate/oversampled_frq)
        sum_sig = numpy.zeros((full_sig_len,))
        s_cnt = 0
        for s in source:
            oversampled_sig = s.tracks[0]     #Сигнал с повышенной частотй дискретизации.
            src_delay = int(round((self.distance_to(s.point)/300.0)*oversampled_frq - s.common_delay*oversampled_frq/self.samplerate))
            oversampled_sig = numpy.hstack((numpy.zeros((src_delay,)), oversampled_sig[0:oversampled_sig.shape[0]-src_delay]))
            mic_input_sig = scipy.signal.resample(oversampled_sig,full_sig_len)
            delay_sig = numpy.zeros((self.dig_delay,))
            source_sig = numpy.hstack((delay_sig, mic_input_sig[0:full_sig_len-self.dig_delay]))*self.amplify
            sum_sig = sum_sig + source_sig

            ms = MicrophoneSignal(self.row, self.col, source_sig, None)
            result_name = "mic " + str(self.row) + " " + str(self.col) + " signal from src " + str(s_cnt)
            self.man.add_data_id(result_name,
                                u'Сигнал на выходе микрофона в позиции ' + str(self.row) + " " + str(self.col) + u"от источника " + str(s_cnt),
                                "signal")
            self.man.push_ticket(ticket.create_ticket(result_name, ms))
            sp_name = "mic " + str(self.row) + " " + str(self.col) + " spectrum from src " + str(s_cnt)
            self.man.add_data_id(sp_name,
                                u'Спектр на выходе микрофона в позиции ' + str(self.row) + " " + str(self.col) + u"от источника " + str(s_cnt),
                                "spectrum")
            self.spectrum(source_sig, sp_name)
            s_cnt +=1 

            
        self.signal = sum_sig
        ms = MicrophoneSignal(self.row, self.col, sum_sig, None)
        self.man.push_ticket(self.man.ticket(self.result_id, ms))

    def receive_wav(self, source, track_number = 0):
        self.signal = source.tracks[track_number]
        ms = MicrophoneSignal(self.row, self.col, self.signal, None)
        self.man.push_data(self.result_id, ms)

    def spectrum(self, sig, spectrum_name, row = None, col = None):
        sig_len = sig.shape[0]
        wnd = 0.54 - 0.46*numpy.cos(2*pi*numpy.arange(sig_len)/sig_len)
        fft_orig = fftshift(fft(sig))/sig_len
        fft_freq = numpy.linspace(-self.samplerate/2, self.samplerate/2, sig_len);
        ss = SignalSpectrum(row, col, fft_freq, fft_orig, None)
        self.man.push_ticket(self.man.ticket(spectrum_name, ss))
    
    def signal_length(self):
        return self.signal.shape[0]
    
    def eval_min_delay(self, source):
        min_dig_distance = float('inf')
        for s in source:
            dig_delay = (self.distance_to(s.point)/300.0)*self.samplerate
            min_dig_distance = min(dig_delay,min_dig_distance)
            
        return int(round(min_dig_distance))


class MicrophoneGrid:
    def __init__(self, manager):
        self.man = manager
        manager.register_handler("grid config", self.handler_config)
        manager.register_handler("simulate", self.handler_simulate)
        manager.register_handler("run-wav", self.handler_run_wav)

        manager.add_data_id("sum signal", u"Суммарный сигнал микрофонной решетки", "signal")
        
    def handler_config(self, ticket):
        self.configure(ticket.get_data())
        self.focus_direction({"phi": 0.0*pi/180.0, "theta":0.0, "L": 10.0})
    
    def handler_simulate(self, ticket):
        self.receive_from(ticket)

    def handler_run_wav(self, source):
        self.receive_wav(source)
        
    def configure(self, grid_config):
        self.cols = grid_config["cols"]
        self.rows = grid_config["rows"]
        if self.cols < 1 or self.rows<1:
            raise ValueError("Нулевая ширина или высота микрофонной решетки")
        if self.cols>1:
            self.delta_x = grid_config["delta_x"]
        else:
            self.delta_x = 0
            
        if self.rows>1:
            self.delta_y = grid_config["delta_y"]
        else:
            self.delta_y = 0
        
        self.x = grid_config["x"]
        self.y = grid_config["y"]
        self.samplerate = grid_config["samplerate"]
        
        self.width  = (self.cols-1) * self.delta_x
        self.height = (self.rows-1) * self.delta_y
        
        self.microphones = range(self.rows)
        for i in range(self.rows):
            self.microphones[i] = range(self.cols)
            for j in range(self.cols):
                try:
                    ampl = grid_config["mic_amplify"][i][j]
                except:
                    ampl = 1.0
                self.microphones[i][j] = Microphone(self.man, i, j,
                                                    self.x+j*self.delta_x - self.width/2,
                                                    self.y+i*self.delta_y - self.height/2,
                                                    self.samplerate,
                                                    ampl)
        
    def print_geometry(self):
        for r in self.microphones:
            for m in r:
                m.print_position()
            sys.stdout.write("\n")
            
    def print_focus_delays(self):
        for r in self.microphones:
            for m in r:
                m.print_timedelay()
            sys.stdout.write("\n")
    
    # Установка координаты начальной точки микрофонной решетки
    def set_position(self, x, y):
        pass
    
    # Установка направления к нормали антенной решетки
    def set_grid_orientation(self, u, v):
        pass
    
    # Фокусировка решетки на выбранной точке пространства
    def focus_direction(self, point):
        L0     = point["L"]
        phi    = point["phi"]
        theta  = point["theta"]
        
        #Положение конца вектора относительно центра решетки
        px = cos(pi/2.0 - phi) * L0;
        py = sin(pi/2.0 - phi) * L0 * sin(theta);
        pz = sin(pi/2.0 - phi) * L0 * cos(theta);
        
        max_delay = 0.0
        for r in self.microphones: # Определяем максимальную задержку распространения
            for m in r:
                L = m.distance_to((px, py, pz)) # Расстояние от микрофона до точки
                t = L / 300.0                # Задержка распространения сигнала
                max_delay = max(max_delay,t)
                
        for r in self.microphones: # Устанавливаем всем элементам задержки, выравнивающие
            for m in r:            # время прохождения сигнала от источника до выхода
                t = m.last_distance() / 300.0
                m.set_time_delay(max_delay - t)
    
    # Прием сигнала из указанных источников. Источников может быть несколько.
    def receive_from(self, ticket):
        #Оцениваем минимальную задержку распространения сигнала от всех источников
        #до всех микрофонов.
        source = ticket.get_data()
        min_dig_delay  = float('inf')
        for r in self.microphones:
            for m in r:
                min_dig_delay = min(m.eval_min_delay(source), min_dig_delay)
                
        min_dig_delay = max(min_dig_delay-1,0)

        #Устанавливаем вычисленную минимальную задержку для всех источников. Её следуеи
        #считать минимальной и вычитать из всех задержек
        s_cnt = 0
        for s in ticket.get_data():
            ms = MicrophoneSignal(None, None, s.tracks[0], None)
            sig_name = "src sig " + str(s_cnt)
            self.man.add_data_id(sig_name, u"Сигнал от источника №" + str(s_cnt), "signal")
            self.man.push_data(sig_name, ms)
            s_cnt += 1

            s.set_common_delay(min_dig_delay)
            
        #Все микрофоны принимают сигнал
        min_received_len = float('inf')
        for r in self.microphones:
            for m in r:
                m.receive_from(ticket)
                min_received_len = min(m.signal_length(), min_received_len)

        self.signal = numpy.zeros((min_received_len,))
        for r in self.microphones:
            for m in r:
                self.signal = self.signal+m.signal[0:min_received_len]
                
        ms = MicrophoneSignal(None, None, self.signal, None)
        self.man.push_ticket(ticket.create_ticket("sum signal", ms))

    # Прием сигнала на микрофона в виде wav-файла для каждого микрофона
    def receive_wav(self, source):
        #Все микрофоны принимают сигнал
        min_received_len = float('inf')
        track_cnt = 0
        for r in self.microphones:
            for m in r:
                m.receive_wav(source, track_cnt)
                track_cnt += 1
                min_received_len = min(m.signal_length(), min_received_len)

        self.signal = numpy.zeros((min_received_len,))
        for r in self.microphones:
            for m in r:
                self.signal = self.signal+m.signal[0:min_received_len]
                
        ms = MicrophoneSignal(None, None, self.signal, None)
        self.man.push_data(self.man.dis.get_data_id("sum signal"), ms)
    
class MicrophoneGridAnalizer:
    def __init__(self, manager):
        self.man = manager
        manager.register_handler("grid config", self.handler_config)
        manager.register_handler("sum signal", self.handler_sum_signal)
        manager.register_handler("sum spectrum", self.handler_sum_spectrum)
        manager.register_handler("rel spectrum flt", self.handler_rel_spectrum)
        manager.register_handler("rel spectrum flt", self.handler_rel_spectrum2d)
        manager.add_data_id("sum spectrum", u"Суммарный сигнал микрофонной решетки", "spectrum")
        manager.add_data_id("spectrum rel", u"Отношение спектров", "spectrum")
        manager.add_data_id("dir spectrum", u"Спектр по направлениям", "spectrum")
        manager.add_data_id("dir spectrum2d", u"Спектр по направлениям", "spectrum")
        manager.add_data_id("frq", u"Частоты, на которых формируется спектр по направлениям", "none")
        
    def handler_config(self, ticket):
        self.configure(ticket.get_data())
        
    def configure(self, grid_config):
        self.cols = grid_config["cols"]
        self.rows = grid_config["rows"]
        self.samplerate = grid_config["samplerate"]
        if self.cols>1:
            self.delta_x = grid_config["delta_x"]
        else:
            self.delta_x = 0
            
        if self.rows>1:
            self.delta_y = grid_config["delta_y"]
        else:
            self.delta_y = 0
        
        for i in range(self.rows):
            for j in range(self.cols):
                mic_sig_name = "mic " + str(i) + " " + str(j) + " signal"
                self.man.register_handler(self.man.dis.get_data_id(mic_sig_name), self.handler_mic_signal)
                result_name = "mic " + str(i) + " " + str(j) + " spectrum"
                self.man.add_data_id(result_name,
                                u'Спектр на выходе микрофона в позиции ' + str(i) + " " + str(j),
                                "spectrum")
    
    def spectrum(self, sig, ticket, spectrum_name, row = None, col = None):
        sig_len = sig.shape[0]
        wnd = 0.54 - 0.46*numpy.cos(2*pi*numpy.arange(sig_len)/sig_len)
        fft_orig = fftshift(fft(sig))/sig_len
        fft_freq = numpy.linspace(-self.samplerate/2, self.samplerate/2, sig_len);
        ss = SignalSpectrum(row, col, fft_freq, fft_orig, None)
        self.man.push_ticket(ticket.create_ticket(spectrum_name, ss))
        return fft_orig
    
    def handler_mic_signal(self, ticket):
        signal = ticket.get_data()
        result_name = "mic " + str(signal.row) + " " + str(signal.col) + " spectrum"
        self.mic_spectrum = self.spectrum(signal.data, ticket, result_name, row=signal.row, col=signal.col)
        
    def handler_sum_signal(self, ticket):
        signal = ticket.get_data()
        self.sum_spectrum = self.spectrum(signal.data, ticket, "sum spectrum")

    def handler_sum_spectrum(self, ticket):
        sum_spectrum = ticket.get_data()
        fft_rel  = (sum_spectrum.get_y() / self.mic_spectrum)#.real
        ss = SignalSpectrum(None, None, sum_spectrum.get_x(), fft_rel, None)
        self.man.push_ticket(ticket.create_ticket("spectrum rel", ss))

        
    def handler_rel_spectrum(self, ticket):
        rel_spectrum = ticket.get_data()
        fft_rel = rel_spectrum.get_y()
        diff_fft = fft_rel - numpy.mean(fft_rel)
        
        sig_len = fft_rel.shape[0]
        x = numpy.linspace(0.0, self.samplerate,sig_len)
        
        npoints = 200*2 #Количество точек в анализируемой полосе частот
        max_fft_freq = (self.delta_x*self.samplerate/300.0)*1.15 #Максимальная частота колебаний отношения спектров
                                                                 #Множитель 1.05 добавлен чтобы чуточку расширить полосу
        fft_freq = numpy.linspace(-max_fft_freq,max_fft_freq, npoints)
        self.man.push_data(self.man.dis.get_data_id("frq"), fft_freq)
        spectrum_dir = numpy.zeros((npoints,))
        spectrum_dir_cmplx = numpy.zeros((npoints,), dtype=complex)
        for i in range(npoints):
            spectrum_dir[i] = abs(numpy.sum(diff_fft*numpy.e**(-2*numpy.pi*1j/self.samplerate*fft_freq[i]*x)))/sig_len
            spectrum_dir_cmplx[i] = numpy.sum(diff_fft*numpy.e**(-2*numpy.pi*1j/self.samplerate*fft_freq[i]*x))/sig_len

        fft_delta_l = fft_freq*300.0/self.samplerate
        fft_angle = self.delta_l_to_alpha(fft_delta_l)

        ss = SignalSpectrum(None, None, fft_angle, spectrum_dir, spectrum_dir_cmplx)
        self.man.push_ticket(ticket.create_ticket("dir spectrum", ss))
        
    def handler_rel_spectrum2d(self, ticket):
        rel_spectrum = ticket.get_data()
        fft_rel = rel_spectrum.get_y()
        diff_fft = fft_rel - numpy.mean(fft_rel)
        
        sig_len = fft_rel.shape[0]
        x = numpy.linspace(0.0, self.samplerate,sig_len)
        
        npoints = 10*2 #Количество точек в анализируемой полосе частот
        max_fft_freq = (self.delta_x*self.samplerate/300.0)*1.15 #Максимальная частота колебаний отношения спектров
                                                                 #Множитель 1.05 добавлен чтобы чуточку расширить полосу
        fft_freq = numpy.linspace(-max_fft_freq,max_fft_freq, npoints)
        self.man.push_data(self.man.dis.get_data_id("frq"), fft_freq)
        spectrum_dir = numpy.zeros((npoints,npoints))
        spectrum_dir_cmplx = numpy.zeros((npoints,npoints), dtype=complex)
        for j in range(npoints):
            for i in range(npoints):
                spectrum_dir[i][j] = abs(numpy.sum(diff_fft*numpy.e**(-2*numpy.pi*1j/self.samplerate*fft_freq[i]-2*numpy.pi*1j/self.samplerate*fft_freq[j]*x)))/sig_len
                spectrum_dir_cmplx[i][j] = numpy.sum(diff_fft*numpy.e**(-2*numpy.pi*1j/self.samplerate*fft_freq[i]-2*numpy.pi*1j/self.samplerate*fft_freq[j]*x))/sig_len

        fft_delta_l = fft_freq*300.0/self.samplerate
        fft_angle = self.delta_l_to_alpha(fft_delta_l)

        ss = SignalSpectrum(None, None, fft_angle, spectrum_dir, spectrum_dir_cmplx)
        self.man.push_ticket(ticket.create_ticket("dir spectrum2d", ss))
    
    # Спектр выходного сигнала
    def spectrum_(self):
        sig_len = self.signal.shape[0]
        wnd = 0.54 - 0.46*numpy.cos(2*pi*numpy.arange(sig_len)/sig_len)
        fft_orig = fftshift(fft(self.signal*wnd))/sig_len
        fft_freq = numpy.linspace(-self.samplerate/2, self.samplerate/2, sig_len);
        return {"x":fft_freq, "y":fft_orig}
    
    # Разность спектров между выходным сигналом и сигналом на микрофоне, принятом за опорный
    def diff_spectrum(self, ref_mic):
        ref_signal = self.microphones[ref_mic[0]][ref_mic[1]].signal
        min_sig_len = min(ref_signal.shape[0], self.signal.shape[0])
        wnd = 0.54 - 0.46*numpy.cos(2*pi*numpy.arange(min_sig_len)/min_sig_len)
        fft_sum  = fftshift(fft(self.signal[0:min_sig_len]*wnd))/min_sig_len
        fft_ref = fftshift(fft(ref_signal[0:min_sig_len]*wnd))/min_sig_len
        fft_rel  = (fft_sum / fft_ref).real
        fft_freq = numpy.linspace(-self.samplerate/2, self.samplerate/2, min_sig_len);
        return {"x":fft_freq, "y":fft_rel}
    
    # Спектр по направлениям на основании выходного сигнала и сигнала, принятого за опорный
    def dir_spectrum(self, ref_mic):
        diff_fft = self.diff_spectrum(ref_mic)["y"].real
        diff_fft -= numpy.mean(diff_fft)
        
        sig_len = self.diff_spectrum(ref_mic)["x"].shape[0]
        x = numpy.linspace(0.0, self.samplerate,sig_len)
        
        npoints = 200 #Количество точек в анализируемой полосе частот
        max_fft_freq = (self.delta_x*self.samplerate/300.0)*1.15 #Максимальная частота колебаний отношения спектров
                                                                 #Множитель 1.05 добавлен чтобы чуточку расширить полосу
        fft_freq = numpy.linspace(0.0,max_fft_freq, npoints)
        self.man.push_data("frq", fft_freq)
        spectrum_dir = numpy.zeros((npoints,))
        for i in range(npoints):
            spectrum_dir[i] = abs(numpy.sum(diff_fft*numpy.e**(-2*numpy.pi*1j/self.samplerate*fft_freq[i]*x)))/sig_len

        fft_delta = fft_freq*300.0/self.samplerate
        fft_angle = self.delta_l_to_alpha(fft_delta)
        return {"x":fft_angle, "y":spectrum_dir}
    
    
    # Функция преобразования разности хода фазового фронта в направление на источник звука
    def delta_l_to_alpha(self, delta):
        #print delta
        S = self.delta_x
        L = 10.0 #FIXME Должно задаваться в виде параметра
        cos_alpha = ((S**2/4.0+L**2)**2-(S**2/4.0+L**2-delta**2/2)**2)**0.5/(S*L)
        #print "cos_alpha", cos_alpha
        alpha = numpy.arccos(numpy.multiply(cos_alpha,numpy.sign(delta))) * 180.0/pi - 90.0
        #print "arc", 90.0 - numpy.arccos(numpy.multiply(cos_alpha,numpy.sign(delta))) * 180.0/pi
        #print alpha
        return alpha
    
    # Получение просуммированного и сфазированного сигнала
    def get_sum_signal(self):
        pass
    
    
class DirSpectrumFilter:
    def __init__(self, manager):
        self.man = manager
        manager.register_handler("spectrum rel", self.handler_spectrum_rel)
        manager.add_data_id("rel spectrum flt", u"Отфильтрованное отношение спектров", "spectrum")
        
    def handler_spectrum_rel(self, ticket):
        rel_sp = ticket.get_data()
        data = rel_sp.get_y()
        data_flt = numpy.array(data)
        for i in range(20,len(data)-20,1):
            data_flt[i] = numpy.median(data[i-20:i+20])
        ss = SignalSpectrum(None, None, rel_sp.get_x(), data_flt, None)
        self.man.push_ticket(ticket.create_ticket("rel spectrum flt", ss))
        
class MaxFind:
    def __init__(self, manager):
        self.man = manager
        manager.register_handler("dir spectrum", self.handler_dir_spectrum)
        manager.register_handler("grid config", self.handler_config)
        manager.register_handler("frq", self.handler_frq)
        manager.register_handler("dir coords", self.handler_dir_coords)
        manager.add_data_id("dir coords sp", u"График максимальных отсчетов по направлениям", "spectrum")
        manager.add_data_id("dir coords", u"Максимальные отсчеты по направлениям", "text")
        manager.add_data_id("rel spectrum rest", u"Восстановленное отношение спектров", "spectrum")
    
    def handler_config(self, ticket):
        config = ticket.get_data()
        self.samplerate = config["samplerate"]
        
    def handler_frq(self, frq):
        self.frq = frq

    def handler_dir_spectrum(self, ticket):
        dir_sp = ticket.get_data()
        data = numpy.array(dir_sp.get_y())
        data_cmplx = dir_sp.tag
        x = dir_sp.get_x()
        max_count = 2
        max_xs = []
        for i in range(0,max_count):
            max_x = numpy.argmax(data)
            max_xs.append((max_x, data[max_x]))
            print "max x", max_x, " max_y", data[max_x]
            for k in range(max_x-1, 1, -1):
                if data[k]>=data[k-1]:
                    data[k] = 0
                else:
                    break
            for k in range(max_x, len(data)-2):
                if data[k]>=data[k+1]:
                    data[k] = 0
                else:
                    break
        data = numpy.zeros(data.shape)
        coords = []
        for p in max_xs:
            data[p[0]] = p[1]
            dc = DirCoord(p[0],data_cmplx[p[0]], self.frq[p[0]], dir_sp.get_x()[p[0]])
            print self.frq[p[0]]
            coords.append(dc)
        ss = SignalSpectrum(None, None, dir_sp.get_x(), data, None)
        self.man.push_ticket(ticket.create_ticket("dir coords sp", ss))
        
        dc = DirCoords(self.samplerate,len(data),coords)
        self.man.push_ticket(ticket.create_ticket("dir coords", dc))
        
    def handler_dir_coords(self, ticket):
        coords = ticket.get_data()
        sig_len = coords.signal_len
        x = numpy.linspace(0.0, self.samplerate,sig_len)
        data = numpy.zeros((sig_len,), dtype=complex)
        for coord in coords.coords:
            data += numpy.e**(2*numpy.pi*1j/self.samplerate*coord.frequency*x)*coord.value
        data += 1
        ss = SignalSpectrum(None, None, None, data, None)
        self.man.push_ticket(ticket.create_ticket("rel spectrum rest", ss))


class RestoreSignal:
    def __init__(self, manager):
        self.man = manager
        manager.register_handler("mic 0 0 spectrum", self.handler_ref_mic_spectrum)
        manager.register_handler("sum spectrum", self.handler_sum_spectrum)
        manager.register_handler("grid config", self.handler_config)
        manager.register_handler("dir coords", self.handler_dir_coords)
        manager.add_data_id("restored spectrum 0", u"Спектр восстановленного сигнала 0", "spectrum")
        manager.add_data_id("restored spectrum 1", u"Спектр восстановленного сигнала 1", "spectrum")
        manager.add_data_id("restored signal 0", u"Восстановленный сигнал от источника 0", "signal")
        manager.add_data_id("restored signal 1", u"Восстановленный сигнал от источника 1", "signal")

    def handler_config(self, ticket):
        grid_config = ticket.get_data()
        self.cols = grid_config["cols"]
        self.rows = grid_config["rows"]
        self.samplerate = grid_config["samplerate"]
        if self.cols>1:
            self.delta_x = grid_config["delta_x"]
        else:
            self.delta_x = 0
            
        if self.rows>1:
            self.delta_y = grid_config["delta_y"]
        else:
            self.delta_y = 0

        self.mic_spectrum = None
        self.coords = None
        self.sum_spectrum = None

    def handler_ref_mic_spectrum(self, ticket):
        mic_sp  = ticket.get_data()
        self.mic_spectrum = mic_sp
        if self.mic_spectrum!=None and self.coords!=None and self.sum_spectrum!=None:
            self.restore_signals(ticket)

    def handler_dir_coords(self, ticket):
        coords = ticket.get_data()
        self.coords = coords.coords
        if self.mic_spectrum!=None and self.coords!=None and self.sum_spectrum!=None:
            self.restore_signals(ticket)

    def handler_sum_spectrum(self, ticket):
        sum_sp = ticket.get_data()
        self.sum_spectrum = sum_sp
        if self.mic_spectrum!=None and self.coords!=None and self.sum_spectrum!=None:
            self.restore_signals(ticket)

    def restore_signals(self, ticket):
        delta_t1 = self.alpha_to_delta_t(self.coords[0].angle)
        delta_t2 = self.alpha_to_delta_t(self.coords[1].angle)
        print "delta_t1", delta_t1, delta_t1 / (1/44100.0)
        print "delta_t2", delta_t2, delta_t2 / (1/44100.0)
        
        A0 = numpy.zeros((len(self.mic_spectrum.get_x()),), dtype=complex)
        A1 = numpy.zeros((len(self.mic_spectrum.get_x()),), dtype=complex)
        for i in range(len(self.mic_spectrum.get_x())):
            frq = self.mic_spectrum.get_x()[i]
            Hm1 = self.mic_spectrum.get_y()[i] * 1j * numpy.sqrt(2.0 * numpy.pi)
            Hsum = self.sum_spectrum.get_y()[i] * 1j * numpy.sqrt(2.0 * numpy.pi)
            if frq <= 70:
                continue

            A0[i] = 2.0 * (Hm1*(1.0+numpy.e**(1j*2.0*numpy.pi*frq*delta_t2)) - Hsum) / (numpy.e**(1j*2.0* numpy.pi*frq*delta_t2) - numpy.e**(1j*2.0* numpy.pi*frq*delta_t1))
            A1[i] = 2.0 * (Hm1*(1.0+numpy.e**(1j*2.0*numpy.pi*frq*delta_t1)) - Hsum) / (numpy.e**(1j*2.0* numpy.pi*frq*delta_t1) - numpy.e**(1j*2.0* numpy.pi*frq*delta_t2))
            if numpy.abs(A0[i])>numpy.abs(Hm1)*10 and numpy.abs(A0[i])>numpy.abs(Hsum)*10:
                A0[i] = 0
                A1[i] = 0
            #if frq>420 and frq < 560:
            #    print frq, Hm1, Hsum, A[i], (1.0+numpy.e**(1j*2.0*numpy.pi*frq*delta_t1))
            if numpy.isnan(A0[i]):
                A0[i] = 0.0
            if numpy.isnan(A1[i]):
                A1[i] = 0.0
        ss = SignalSpectrum(None, None, self.mic_spectrum.get_x(), A0, None)
        self.man.push_ticket(ticket.create_ticket("restored spectrum 0", ss))
        ss = SignalSpectrum(None, None, self.mic_spectrum.get_x(), A1, None)
        self.man.push_ticket(ticket.create_ticket("restored spectrum 1", ss))

        sp = fftshift(A0)
        sig = -ifft(sp)
        sig = sig.real
        ms = MicrophoneSignal(None, None, sig, None)
        self.man.push_ticket(ticket.create_ticket("restored signal 0", ms))

        sp = fftshift(A1)
        sig = -ifft(sp)
        sig = sig.real
        ms = MicrophoneSignal(None, None, sig, None)
        self.man.push_ticket(ticket.create_ticket("restored signal 1", ms))

    def alpha_to_delta_t(self, alpha):
        a = (alpha + 90.0) / 180.0 * numpy.pi
        S = self.delta_x
        L = 10 #FIXME Должно задаваться в виде параметра
        delta_l = numpy.sqrt(S*S/4.0+S*L*numpy.cos(a)+L*L) - numpy.sqrt(S*S/4.0-S*L*numpy.cos(a)+L*L)
        delta_t = delta_l / 300.0
        #print "alpha", alpha
        #print "delta_t", delta_t
        #if alpha > 0:
        #    return -delta_t
        return -delta_t

def list_adons():
    return ['Microphone', 'MicrophoneGrid', 'MicrophoneGridAnalizer', 'DirSpectrumFilter', 'RestoreSignal', 'MaxFind']

def load_adons(manager, adon_list = None):
    adons = {}
    adons["mgrid"] = MicrophoneGrid(manager)
    adons["analyzer"] = MicrophoneGridAnalizer(manager)
    adons["rel_flt"] = DirSpectrumFilter(manager)
    adons["max_find"] = MaxFind(manager)
    adons["restore_signal"] = RestoreSignal(manager)
    return adons


def init_module(manager, gui):
    adons = []
    adons.append(MicrophoneGrid(manager))
    adons.append(MicrophoneGridAnalizer(manager))
    adons.append(DirSpectrumFilter(manager))
    adons.append(MaxFind(manager))
    adons.append(RestoreSignal(manager))
    return adons
    