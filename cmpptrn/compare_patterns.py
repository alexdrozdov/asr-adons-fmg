#!/usr/bin/env python
# -*- coding: utf-8 -*-

import localdb
import manager
import wx
import compare_patterns_interface

def pcmp(x,y):
    return cmp(x[0],y[0])

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
        self.refresh()
        
    def _refresh_order_by_name(self):
        if self.gridCmpResults.GetNumberRows()>0:
            self.gridCmpResults.DeleteRows(0, self.gridCmpResults.GetNumberRows())
        if self.gridCmpResults.GetNumberCols()>0:
            self.gridCmpResults.DeleteCols(0, self.gridCmpResults.GetNumberCols())
        self.gridCmpResults.AppendCols(1+len(self.columns))
        self.gridCmpResults.AppendRows(len(self.results))
        self.gridCmpResults.SetColLabelValue(0, u'Смещение')
        for i in range(len(self.columns)):
            self.gridCmpResults.SetColLabelValue(i+1, self.columns[i])
        for i in range(len(self.results)):
            j = 1
            self.gridCmpResults.SetCellValue(i,0, str(self.results[i].global_offset))
            for k in self.results[i].probabilities.values():
                self.gridCmpResults.SetCellValue(i,j,str(k))
                j += 1
    def _refresh_order_by_probability(self):
        if self.gridCmpResults.GetNumberRows()>0:
            self.gridCmpResults.DeleteRows(0, self.gridCmpResults.GetNumberRows())
        if self.gridCmpResults.GetNumberCols()>0:
            self.gridCmpResults.DeleteCols(0, self.gridCmpResults.GetNumberCols())
        self.gridCmpResults.AppendCols(1+len(self.columns))
        self.gridCmpResults.AppendRows(len(self.results))
        self.gridCmpResults.SetColLabelValue(0, u'Смещение')
        for i in range(len(self.columns)):
            self.gridCmpResults.SetColLabelValue(i, str(i+1))
        for i in range(len(self.results)):
            j = 1
            self.gridCmpResults.SetCellValue(i,0, str(self.results[i].global_offset))
            p = self.results[i].probabilities
            m = [(p[x],x) for x in p.keys()]
            m.sort(pcmp)
            for k in m:
                self.gridCmpResults.SetCellValue(i,j,str(k[1]))
                j += 1
    
    def refresh(self):
        if 0==self.comboViewBy.Selection:
            self._refresh_order_by_name()
        else:
            self._refresh_order_by_probability()

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

