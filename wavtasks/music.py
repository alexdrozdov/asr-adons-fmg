#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import numpy
import pylab
import scipy, scipy.io.wavfile, scipy.signal
from numpy.fft import *
from math import sin, cos, pi, sqrt
from exceptions import ValueError

import wav_source

class Note:
    def __init__(self, predecessor):
        self._frequency = 0
        self._predecessor = predecessor
        self._follower = None
        self._octave = 0;
        self._halfton = 0
        self._name    = 0
        self._harmonics = 1
        
        if predecessor:
            predecessor._follower = self
            self._offset = predecessor._offset + 1
            self._frequency = predecessor._frequency * predecessor._halfton
            self._halfton = predecessor._halfton
            self._harmonics = predecessor._harmonics
            next_note_name = {
                "C" : ("C#",0),
                "C#" : ("D",0),
                "D" : ("D#",0),
                "D#" : ("E",0),
                "E" : ("F",0),
                "F" : ("F#",0),
                "F#" : ("G",0),
                "G" : ("G#",0),
                "G#" : ("A",0),
                "A" : ("A#",0),
                "A#" : ("B",0),
                "B" : ("C",1)
            }
            self._name = next_note_name[predecessor._name][0]
            self._octave = predecessor._octave + next_note_name[predecessor._name][1]
        else:
            self._offset = 0
    
    def name_get(self):
        return self._name
    def name_set(self, nm):
        self._name = nm
    
    def frequency_set(self,value):
        self._frequency = value
    def frequency_get(self):
        return self._frequency
    
    def next_note_get(self, offs = 1):
        n = self
        for ii in range(offs):
            n = n._follower
        return n
    
    def halfton_set(self, delta_f):
        self._halfton = delta_f
    def halfton_get(self):
        return self._halfton
    
    def octave_set(self, oct):
        self._octave = oct
    def octave_get(self):
        return self._octave
    
    def harmonics_set(self, n):
        self._harmonics = n
    def harmonics_get(self):
        return self._harmonics
    
    def generate(self, samplerate, length):
        x = 2*numpy.pi*numpy.arange(length)/samplerate
        y = numpy.sin(x*self._frequency)
        for h in range(self._harmonics):
            y += numpy.sin(x*self._frequency*(h+2))/float(h+2)**3
        
        y /= float(self._harmonics+1)
        
        xx = -numpy.linspace(0,3,length)-0.25
        envelop = (4.0-4.0*numpy.cos(2.0*numpy.pi*numpy.e**xx))/10.0
        #envelop = numpy.linspace(0.0,1.0, length)
        y *= envelop
        
        return y
    
    
class Interval:
    def __init__(self, spec):
        spec_opts = spec.split(' ')
        self.interval = -1
        self.name = spec
        if spec_opts[1] == "прима":
            if spec_opts[0] == "чистая":
                self.interval =  0
            elif spec_opts[0]=="увеличенная":
                self.interval =  1
        elif spec_opts[1] == "секунда":
            if spec_opts[0] == "уменьшенная":
                self.interval =  0
            elif spec_opts[0]=="малая":
                self.interval =  1
            elif spec_opts[0]=="большая":
                self.interval =  2
            elif spec_opts[0]=="увеличенная":
                self.interval =  3
        elif spec_opts[1] == "терция":
            if spec_opts[0] == "уменьшенная":
                self.interval =  2
            elif spec_opts[0]=="малая":
                self.interval =  3
            elif spec_opts[0]=="большая":
                self.interval =  4
            elif spec_opts[0]=="увеличенная":
                self.interval =  5
        elif spec_opts[1] == "кварта":
            if spec_opts[0] == "уменьшенная":
                self.interval =  4
            elif spec_opts[0]=="чистая":
                self.interval =  5
            elif spec_opts[0]=="увеличенная":
                self.interval =  6
        elif spec_opts[1] == "квинта":
            if spec_opts[0] == "уменьшенная":
                self.interval =  6
            elif spec_opts[0]=="чистая":
                self.interval =  7
            elif spec_opts[0]=="увеличенная":
                self.interval =  8
        elif spec_opts[1] == "секста":
            if spec_opts[0] == "уменьшенная":
                self.interval =  7
            elif spec_opts[0]=="малая":
                self.interval =  8
            elif spec_opts[0]=="большая":
                self.interval =  9
            elif spec_opts[0]=="увеличенная":
                self.interval =  10
        elif spec_opts[1] == "септима":
            if spec_opts[0] == "уменьшенная":
                self.interval =  9
            elif spec_opts[0]=="малая":
                self.interval =  10
            elif spec_opts[0]=="большая":
                self.interval =  11
            elif spec_opts[0]=="увеличенная":
                self.interval =  12
        elif spec_opts[1] == "октава":
            if spec_opts[0] == "уменьшенная":
                self.interval =  11
            elif spec_opts[0]=="чистая":
                self.interval =  12
            elif spec_opts[0]=="увеличенная":
                self.interval =  13
        else:
            pass
        
        if self.interval < 0:  
            raise ValueError("Неизвестная спецификация интервала")
    
    def intervals_get(self):
        return self.interval
    intervals = property(intervals_get)


class WavSound:
    def __init__(self, *args):
        if 2==len(args):
            self.__init__snd(args[0], args[1])
        elif 1==len(args):
            self.__init__wav(args[0])
        else:
            raise ValueError("Недопутимые параметры вызова конструктора WavSound")
    
    def __init__wav(self, wavname):
        ws = wav_source.WavSource({"wavname" : wavname})
        self.__init__snd(ws.samplerate, ws.tracks[0]/32768.0)
    
    def __init__snd(self, samplerate, sound):
        self._samplerate = samplerate
        self._sound = sound
        
        self._fft_freq = None
        self._fft_orig = None

    def copy(self):
        return WavSound(self.samplerate(), self._sound)
        
    def samplerate(self):
        return self._samplerate
        
    def time(self):
        return self._sound.shape[0]/float(self._samplerate)
        
    def generate_timeline(self):
        return numpy.arange(self._sound.shape[0])/float(self._samplerate)
        
    def plot(self, noshow=False):
        x = numpy.arange(self._sound.shape[0])/float(self._samplerate)
        pylab.plot(x,self._sound)
        if not noshow:
            pylab.show()
        
    def plot_spectrum(self):
        if not self._fft_freq or not self._fft_orig:
            self.spectrum()
        pylab.plot(self._fft_freq, numpy.log(self._fft_orig))
        pylab.show()
        
    def repeat(self, count):
        self._sound = numpy.tile(self._sound, count)
        
    def extend(self, new_length=None, percent=None):
        if None==new_length and None==percent:
            raise "Не указана длина результата или процентное соотношение"
        if None!=new_length and None!=percent:
            raise "Указаны взаимоисключающие параметры - длина и процентное соотношение"
        if None!=percent:
            new_length = int(self.length()*percent)
        self._sound = numpy.resize(self._sound, new_length)
    
    def invert(self):
        self._sound = self._sound * -1.0
        
    def apply_filter(self,flt_param):
        (b,a) = flt_param
        self._sound = scipy.signal.lfilter(b,a,self._sound)
        
    # Спектр выходного сигнала
    def spectrum(self):
        sig_len = self._sound.shape[0]
        wnd = 0.54 - 0.46*numpy.cos(2*pi*numpy.arange(sig_len)/sig_len)
        self._fft_orig = abs(fftshift(fft(self._sound*wnd))/sig_len)
        self._fft_freq = numpy.linspace(-self._samplerate/2, self._samplerate/2, sig_len);
    
    def save(self, filename, ampl = 1.0):
        scipy.io.wavfile.write(filename,
                               self._samplerate,
                               numpy.int16(self._sound*32767.0*ampl))
    
    def play(self, ampl = 1.0):
        self.save('tmp.wav',  ampl = ampl)
        os.popen("aplay tmp.wav")
        
    def length(self):
        return self._sound.shape[0]
        

class NoteList:
    def __init__(self, octave, base_frequency, halftone, count):
        self.tonika = Note(None)
        self.tonika.name_set("C")
        self.tonika.frequency_set( base_frequency)
        self.tonika.halfton_set(halftone)
        self.tonika.octave_set(octave)
        self.tonika.harmonics_set(2)
        
        cur_note = self.tonika
        self._list = {}
        self._list[(cur_note.octave_get(), cur_note.name_get())] = cur_note
        for ii in range(count):
            cur_note = Note(cur_note)
            self._list[(cur_note.octave_get(), cur_note.name_get())] = cur_note
            
    def build_accord(self, base, intervals, accord = None):
        base_note = self._list[base]
        acc = []
        acc.append(base_note)
        for intrv in intervals:
            acc.append(base_note.next_note_get(intrv.intervals_get()))
            
        if accord:
            acc.extend(accord)
            
        return acc
    
    def generate_accord(self, samplerate, length, accord):
        y = numpy.zeros((length,))
        note_power = 1.0
        part_offs = 0
        for note in accord:
            y[part_offs:] += (note.generate(samplerate, length)*note_power)[part_offs:]
            #part_offs = int((part_offs+length)/2)
            note_power *- 0.9
            
        y /= float(len(accord))
            
        return WavSound(samplerate, y)
        
    
def main():
    notelist = NoteList(1, 440.0*2.0**(-9.0/12.0), 2.0**(1.0/12.0), 20)
    
    int_0 = Interval("большая терция")
    int_1 = Interval("малая терция")
    int_2 = Interval("чистая квинта")
    
    acc_minor = notelist.build_accord((1,"F",), (int_1,int_2))
    acc_major = notelist.build_accord((1,"F",), (int_0,int_2))
    
    sound_minor = notelist.generate_accord(44100, 88200, acc_minor)
    sound_major = notelist.generate_accord(44100, 88200, acc_major)
    
    sound_minor.save("c_minor.wav")
    sound_major.save("c_major.wav")
    
if __name__ == "__main__":
    main()