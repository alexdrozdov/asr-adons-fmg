#!/usr/bin/env python
# -*- coding: utf-8 -*-

import localdb
import manager
import wx
import compare_patterns_interface

class CompareResultsInst(compare_patterns_interface.CompareResultsFrame):
    def __init__(self, manager):
        self.man = manager
        compare_patterns_interface.CompareResultsFrame.__init__(self, None, -1, "")
        self.man.register_handler("matrix_compare-result", self.handle_compare_result)
        self.columns = []
        self.results = []
        
    def handle_compare_result(self, ticket):
        cr = ticket.get_data()
        self.results.append(cr)
        for k in cr.probabilities.keys():
            if k not in self.columns:
                self.columns.append(k)
        
    def btnRefresh_on_click(self, event):  # wxGlade: CompareResultsFrame.<event_handler>
        #FIXME Блокировать добавление новых эелементов в список - возможны сбои при обновлении в процессе вычислений
        if self.gridCmpResults.GetNumberRows()>0:
            self.gridCmpResults.DeleteRows(0, self.gridCmpResults.GetNumberRows())
        if self.gridCmpResults.GetNumberCols()>0:
            self.gridCmpResults.DeleteCols(0, self.gridCmpResults.GetNumberCols())
        self.gridCmpResults.AppendCols(len(self.columns))
        self.gridCmpResults.AppendRows(len(self.results))
        for i in range(len(self.columns)):
            self.gridCmpResults.SetColLabelValue(i, self.columns[i])
        for i in range(len(self.results)):
            j = 0
            for k in self.results[i].probabilities.values():
                self.gridCmpResults.SetCellValue(i,j,str(k))
                j += 1

    def btnClear_on_click(self, event):  # wxGlade: CompareResultsFrame.<event_handler>
        print "Event handler 'btnClear_on_click' not implemented!"
        event.Skip()

    def btnSave_on_click(self, event):  # wxGlade: CompareResultsFrame.<event_handler>
        print "Event handler 'btnSave_on_click' not implemented!"
        event.Skip()

    def btnLoad_on_click(self, event):  # wxGlade: CompareResultsFrame.<event_handler>
        print "Event handler 'btnLoad_on_click' not implemented!"
        event.Skip()

    def gridCmpResults_on_cell_select(self, event):  # wxGlade: CompareResultsFrame.<event_handler>
        print "Event handler 'gridCmpResults_on_cell_select' not implemented!"
        event.Skip()


def init_module(manager, gui):
    frame = CompareResultsInst(manager)
    gui.register_window(frame, u"Результаты сравнения шаблонов", "wnd_pattern-cmp-results")
    return [frame,]

