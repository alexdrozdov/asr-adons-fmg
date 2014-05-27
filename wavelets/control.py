#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx, control_interface, sys, os
from wav_source import *

class ControlFrameInst(control_interface.ControlFrame):
    def __init__(self, manager):
    	self.man = manager
        control_interface.ControlFrame.__init__(self, None, -1, "")
        self.Bind(wx.EVT_CLOSE, self.btnClose_handler, self)
        self.control = None
        try:
            with open("control_file_name", 'r') as fd_def_file:
                file_path = fd_def_file.readline()
                try:
                    with open(file_path, 'r') as fd:
                        self.control = fd.read()
                    self.file_path = file_path
                except:
                    pass
        except:
            pass
    def btnLoad_handler(self, event):
    	file_path = str(self.choose_file(u"Выберите файл с управлением"))
        try:
            with open(file_path, 'r') as fd:
                self.control = fd.read()
            fd_def_file = open("control_file_name", 'w')
            fd_def_file.write(file_path)
            fd_def_file.close()
            self.file_path = file_path
        except:
            pass
        event.Skip()

    def btnExecute_handler(self, event):  # wxGlade: FmgFrame.<event_handler>
        try:
            with open(self.file_path, 'r') as fd:
                self.control = fd.read()
        except:
            wx.MessageBox('Сбой при открытии файла с управлением', 'Не загружено управление', wx.OK | wx.ICON_ASTERISK)
            event.Skip()
            return
        if not self.control:
            wx.MessageBox('Перед исполнением управления его необходимо загрузить из файла', 'Не загружено управление', wx.OK | wx.ICON_ASTERISK)
            event.Skip()
            return
        exec(self.control)

    def btnClose_handler(self, event):
    	pass

    def choose_file(self, msg):
        """ Ф-ция открывает диалог проводника """

        wildcard = "Техт Files (*.txt)|*.dat;*.prn;*.txt|"\
        "All files (*.*)|*.*"
        dialog = wx.FileDialog(None, msg, os.getcwd(),"", wildcard, wx.OPEN|wx.MULTIPLE)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
        dialog.Destroy()
        return path

def init_module(manager, gui):
    frame = ControlFrameInst(manager)
    gui.register_window(frame, "Задания для распознавания", "wnd_wavelet-asr")
    return [frame,]
