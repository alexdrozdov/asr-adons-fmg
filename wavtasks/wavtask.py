#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx, wavtasks_interface, sys, os
import localdb
from wav_source import *
import music
import os.path

class WavTasksInst(wavtasks_interface.WavTasks):
    def __init__(self, manager):
    	self.man = manager
        wavtasks_interface.WavTasks.__init__(self, None, -1, "")
        self.Bind(wx.EVT_CLOSE, self.btnClose_handler, self)
        self.file_list = []
        try:
        	self.file_list = localdb.db.read_value("/db/persistent/wavtasks/file_list")
        except:
        	pass
        self.show_list()
    def show_list(self): 
    	self.lbWavFiles.SetItems(self.file_list)

    def btnClose_handler(self, event):
    	self.Hide()
    def get_user_load_path(self):
        user_load_path = os.path.expanduser('~/')
        try:
            user_load_path = localdb.db.read_value('/db/persistent/wavtasks/default_load_path')
        except:
            pass
        return user_load_path
    def btnAddFiles_handler(self, event):
    	filename = None
        wildcard = u"Аудиофайлы (*.wav)|*.wav|Все файлы  (*.*)|*.*"
        dialog = wx.FileDialog(None, u"Загрузить Wav-файл для обработки", self.get_user_load_path(),"", wildcard, wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetPath()
            user_load_path = os.path.dirname(os.path.realpath(filename))
            localdb.db.write_persistent('/db/persistent/wavtasks/default_load_path', user_load_path)
        dialog.Destroy()
        if None == filename:
            return
        if filename in self.file_list:
        	return
        self.file_list.append(filename)
        localdb.db.write_persistent("/db/persistent/wavtasks/file_list", self.file_list)
        self.show_list()

    def btnRemoveFiles_handler(self, event):
		try:
			sel = self.lbWavFiles.GetSelections()
			file_names = self.lbWavFiles.GetItems()
			remove_names = []
			for s in sel:
				remove_names.append(file_names[s])
			for f in remove_names:
				self.file_list.remove(f)
			localdb.db.write_persistent("/db/persistent/wavtasks/file_list", self.file_list)
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
        localdb.db.write_persistent("/db/persistent/wavtasks/file_list", self.file_list)
        self.show_list()
        self.lbWavFiles.SetSelection(sel-1)

    def btnMoveDown_handler(self, event):  # wxGlade: WavTasks.<event_handler>
        sel = self.lbWavFiles.GetSelection()
        if sel >= len(self.file_list)-1:
        	return
        v = self.file_list[sel]
        self.file_list.remove(v)
        self.file_list.insert(sel+1, v)
        localdb.db.write_persistent("/db/persistent/wavtasks/file_list", self.file_list)
        self.show_list()
        self.lbWavFiles.SetSelection(sel+1)
    def btnExecute_handler(self, event):  # wxGlade: WavTasks.<event_handler>
        #Параметры решетки
		swt_config = {"family"         : "bior2.4",
		               "max_level"  : 11,
		               "reshape-method" : "multiline_resize",
		               "reshape-size" : [300,-1],
		               "reshape-vflip" : True}

		self.man.push_ticket(self.man.ticket("swt config", swt_config, description=u"Параметры wavelet-преобразования"));
		for f in self.file_list:
			ws_0 = music.WavSound(f)
			self.man.push_ticket(self.man.ticket("run", ws_0, description=os.path.basename(f)))

def init_module(manager, gui):
    frame = WavTasksInst(manager)
    gui.register_window(frame, u"Обработка wav-файлов", "wnd_wav-asr")
    return [frame,]