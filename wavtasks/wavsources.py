            #!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx, wavsources_interface, sys, os
import localdb
from wav_source import *
import music
import os.path
from math import sin, cos, pi, sqrt

def p2c(point):
    try:
        angle_measure = point["measure"]
    except:
        angle_measure = "rad"
    
    phi = point["phi"]
    theta = point["theta"]
    L = point["L"]
    
    if "deg"==angle_measure:
        phi *= pi/180.0
        theta *= pi/180.0
    
    px = cos(pi/2.0 - phi) * L;
    py = sin(pi/2.0 - phi) * L * sin(theta);
    pz = sin(pi/2.0 - phi) * L * cos(theta);
    return (px, py,pz)

class WavSourceEntry:
    def __init__(self, filename, phi, theta, l):
        self.filename = filename
        self.phi = phi
        self.theta = theta
        self.l = l
    def update(self, phi, theta):
        self.phi = phi
        self.theta = theta

class WavSourcesInst(wavsources_interface.WavSources):
    def __init__(self, manager):
    	self.man = manager
        wavsources_interface.WavSources.__init__(self, None, -1, "")
        self.Bind(wx.EVT_CLOSE, self.btnClose_handler, self)
        self.file_list = []
        try:
            self.load_file_list()
            self.show_list()
            if len(self.file_list)>1:
                self.lbWavFiles.SetSelection(0  )
        except:
        	pass
    def show_list(self): 
        l = []
        for e in self.file_list:
            l.append(e.filename)
    	self.lbWavFiles.SetItems(l)

    def btnClose_handler(self, event):
    	self.Hide()
    def get_user_load_path(self):
        user_load_path = os.path.expanduser('~/')
        try:
            user_load_path = localdb.db.read_value('/db/persistent/wavsources/default_load_path')
        except:
            pass
        return user_load_path
    def findfile(self, filename):
        for e in self.file_list:
            if e.filename == filename:
                return e
        return None
    def save_file_list(self):
        l = []
        for e in self.file_list:
            l.append([e.filename, e.phi, e.theta, e.l])
        localdb.db.write_persistent("/db/persistent/wavsources/file_list", l)
            
    def load_file_list(self):
        l = localdb.db.read_value("/db/persistent/wavsources/file_list")
        for e in l:
            self.file_list.append(WavSourceEntry(e[0], e[1], e[2], e[3]))
    
    def btnAddFiles_handler(self, event):
    	filename = None
        wildcard = u"Аудиофайлы (*.wav)|*.wav|Все файлы  (*.*)|*.*"
        dialog = wx.FileDialog(None, u"Загрузить Wav-файл для обработки", self.get_user_load_path(),"", wildcard, wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetPath()
            user_load_path = os.path.dirname(os.path.realpath(filename))
            localdb.db.write_persistent('/db/persistent/wavsources/default_load_path', user_load_path)
        dialog.Destroy()
        if None == filename:
            return
        if None != self.findfile(filename):
        	return
        fe = WavSourceEntry(filename, 0.0, 0.0, 10.0)
        self.file_list.append(fe)
        self.save_file_list()
        self.show_list()

    def btnRemoveFiles_handler(self, event):
        try:
            sel = self.lbWavFiles.GetSelection()
            self.file_list.pop(sel)
            self.save_file_list()
            self.show_list()
        except:
        	pass
        self.show_list()

    def btnMoveUp_handler(self, event):  # wxGlade: WavTasks.<event_handler>
        sel = self.lbWavFiles.GetSelection()
        if sel < 1:
        	return
        v = self.file_list[sel]
        self.file_list.remove(v)
        self.file_list.insert(sel-1, v)
        self.save_file_list()
        self.show_list()
        self.lbWavFiles.SetSelection(sel-1)

    def btnMoveDown_handler(self, event):  # wxGlade: WavTasks.<event_handler>
        sel = self.lbWavFiles.GetSelection()
        if sel >= len(self.file_list)-1:
        	return
        v = self.file_list[sel]
        self.file_list.remove(v)
        self.file_list.insert(sel+1, v)
        self.save_file_list()
        self.show_list()
        self.lbWavFiles.SetSelection(sel+1)
    def btnExecute_handler(self, event):
        ws_list = []
        for e in self.file_list:
            ws = WavSource({"point":   p2c( { "phi"     : e.phi,
                                    "theta"   : e.theta,
                                    "L"       : e.l,
                                    "measure" : "deg"}),
                "wavname"    : e.filename,
                "samplerate" : 44100*5})
            ws_list.append(ws)
        ws_tuple = tuple(ws_list)
        gconfig = {"x"       : 0.0,
               "y"       : 0.0,
               "cols"    : 2,
               "rows"    : 2,
               "delta_x" : 0.2,
               "delta_y" : 0.2,
               "samplerate" : 44100,
               "ref_mics" : ((0,0),(0,1),(1,0),(1,1))}

        self.man.push_ticket(self.man.ticket("grid config", gconfig, u"Grid config"))
        self.man.push_ticket(self.man.ticket("simulate", ws_tuple, u'Симуляция'))

    def lbWavFiles_on_click(self, event):
        itm = self.lbWavFiles.GetSelection()
        e = self.file_list[itm]
        self.textPhi.SetValue(str(e.phi))
        self.textTheta.SetValue(str(e.theta))
        self.textL.SetValue(str(e.l))
        
    def textPhi_on_enter(self, event): # wxGlade: WavSources.<event_handler>
        v = float(self.textPhi.GetValue())
        itm = self.lbWavFiles.GetSelection()
        e = self.file_list[itm]
        e.phi = v
        self.save_file_list()
    def textTheta_on_enter(self, event): # wxGlade: WavSources.<event_handler>
        v = float(self.textTheta.GetValue())
        itm = self.lbWavFiles.GetSelection()
        e = self.file_list[itm]
        e.theta = v
        self.save_file_list()
    def textL_on_enter(self, event): # wxGlade: WavSources.<event_handler>
        v = float(self.textL.GetValue())
        itm = self.lbWavFiles.GetSelection()
        e = self.file_list[itm]
        e.l = v
        self.save_file_list()

def init_module(manager, gui):
    frame = WavSourcesInst(manager)
    gui.register_window(frame, "Обработка wav-файлов для ФМР", "wnd_wav-fmg")
    return [frame,]