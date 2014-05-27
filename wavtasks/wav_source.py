#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy
import scipy, scipy.io.wavfile, scipy.signal

class WavSource:
    def __init__(self, src_config):
        self.common_delay = 0        
        try:
            self.point = src_config["point"]
        except:
            self.point = (0.0,0.0,0.0)
        try:
            self.requred_samplerate = src_config["samplerate"]
            self.resample = True
        except:
            self.requred_samplerate = 0
            self.resample = False
        try:
            self.amplify = src_config["amplify"]
        except:
            self.amplify = 1.0
        
        load_from_file = False
        try:
            self.wavname = src_config["wavname"]
            load_from_file = True
            (self.samplerate, self.wavdata) = scipy.io.wavfile.read(self.wavname)
            self.tracks = []
            for i in range(len(self.wavdata.shape)):
                self.tracks.append(numpy.array(self.wavdata[:,i],dtype=float)*self.amplify)
                
            self.length = self.tracks[0].shape[0]
            
            if self.resample and self.samplerate!=self.requred_samplerate:
                #Необходима передискретизация
                resampled_samples = self.length*self.requred_samplerate/self.samplerate
                for i in range(len(self.tracks)):
                    self.tracks[i] = scipy.signal.resample(self.tracks[i], resampled_samples)
                self.samplerate = self.requred_samplerate
                self.length = resampled_samples
        except:
            if load_from_file:
                raise "Couldnt load wav file"+self.wavname
            self.tracks = []
            self.tracks.append(src_config["track"])
            self.samplerate = src_config["samplerate"]
            self.length = self.tracks[0].shape
        
    def set_common_delay(self, delay):
        self.common_delay = delay

    def save_to_file(self, filename):
        scipy.io.wavfile.write(filename, self.samplerate, self.tracks[0])

    def get_track_count(self):
        return len(self.tracks)
        
    def plot(self):
        pass
        
    def print_info(self):
        print "point:", self.point
        print "samplerate:", self.samplerate
        print "length:", self.length
        