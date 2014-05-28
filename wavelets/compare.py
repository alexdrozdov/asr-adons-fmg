#!/usr/bin/env python
# -*- #coding: utf8 -*-

import numpy
import copy
from matplotlib import pyplot
import scipy
import scipy.signal
import traceback
import pprint
import pickle
import folderscan

class Log:
    All = 0
    Medium = 1
    Critical = 2
    SelectedOnly = 3
    Always = 4
    def __init__(self, details_level = Critical):
        self.details_level = details_level
    def log(self, level, *arg):
        if level < self.details_level:
            return
        s = ""
        for a in arg:
            s += pprint.pformat(a) + ' '
        print s
        
log = Log(Log.Critical)

class Fragment:
    min_to_max = 1
    max_to_min = 2
    def __init__(self, frag_type, l, r, complete_sig=None, sig=None):
        try:
            self.l = l
            self.r = r
            self.ll = r-l
            if None!=complete_sig:
                self.sig = complete_sig[l:r]
            else:
                self.sig = sig
            self.frag_type = frag_type
            s_min = min(self.sig)
            s_max = max(self.sig)
            self.sig_norm = (self.sig-s_min) / (s_max-s_min)
        except:
            print frag_type,l,r,complete_sig[l:r]
            print traceback.format_exc()
            raise ValueError()
            
    def compare_with(self, fragments):
        if isinstance(fragments, list):
            log.log(Log.All, len(fragments))
            log.log(Log.All, fragments[0].sig.shape,fragments[1].sig.shape,fragments[2].sig.shape)
            sig = numpy.hstack((fragments[0].sig, fragments[1].sig, fragments[2].sig))
            log.log(Log.All, sig.shape)
            #exit(0)
            fragment=Fragment(fragments[0].frag_type, fragments[0].l, fragments[-1].r, sig=sig)
        else:
            fragment = fragments
        max_ll = max(self.ll, fragment.ll)
        f1 = scipy.signal.resample(self.sig_norm, max_ll)
        f2 = scipy.signal.resample(fragment.sig_norm, max_ll)
        return {"diff" : numpy.sum((f1-f2)**2.0) / float(max_ll),
                "scale": float(self.ll) / float(fragment.ll)}
    def print_fragment(self):
        log.log(Log.Always, "Left:", self.l, "Right:", self.r, "Type:", str(self.frag_type), "Values:", self.sig[0],":",self.sig[-1])
        
class FragmentList:
    def __init__(self, fragments):
        self.fragments = fragments
        s_min =  10000000
        s_max = -10000000
        for f in self.fragments:
            s_min = min(s_min, min(f.sig))
            s_max = max(s_max, max(f.sig))
        self.s_min = s_min
        self.s_max = s_max
        self.s_delta = s_max-s_min
    def compare_with(self, fragment_list):
        if len(self.fragments) != len(fragment_list.fragments):
            print "Fragment list length mismatch"
            return 0
        diff = 0.0
        scales = []
        for i in range(len(self.fragments)):
            f1 = self.fragments[i].sig
            f2 = fragment_list.fragments[i].sig
            f1 = (f1-self.s_min) / self.s_delta
            f2 = (f2-fragment_list.s_min) / fragment_list.s_delta
            max_ll = max(self.fragments[i].ll, fragment_list.fragments[i].ll)
            f1 = scipy.signal.resample(f1, max_ll)
            f2 = scipy.signal.resample(f2, max_ll)
            diff += numpy.sum((f1-f2)**2.0) / float(max_ll)
            scales.append(float(self.fragments[i].ll) / float(fragment_list.fragments[i].ll))
        return {"diff" : diff,
                "scales": scales}

class SigPattern:
    default_options = {
        "fine-for-scaling" : True,
        "fine-for-inlinear-scaling" : True,
        "fine-amplitude" : False,
        "fine-for-uncompared": True
                       }
    def __init__(self, sig):
        self.sig = sig
        self.fragments = []
        #log.log(Log.All, "Signal to build", sig)
    def find_max(self):
        s = self.sig
        s0 = s[0:-5]
        s1 = s[1:-4]
        s2 = s[2:-3]
        s3 = s[3:-2]
        s4 = s[4:-1]
        s_max = (s2>s0) * (s2>s1)* (s2>s3) * (s2>s4)
        s_max = numpy.nonzero(s_max)[0]
        s_max += 2
        self.s_max = s_max
        log.log(Log.All, "s_max", s_max)
    def find_min(self):
        s = self.sig
        s0 = s[0:-5]
        s1 = s[1:-4]
        s2 = s[2:-3]
        s3 = s[3:-2]
        s4 = s[4:-1]
        s_min = (s2<s0) * (s2<s1)* (s2<s3) * (s2<s4)
        s_min = numpy.nonzero(s_min)[0]
        s_min += 2
        self.s_min = s_min
        log.log(Log.All, "s_min", s_min)
    def print_fragments(self):
        for f in self.fragments:
            f.print_fragment()
            
    def compare(self, sp):
        try:
            f_count = len(self.fragments)
            f_sp_count = len(sp.fragments)
            log.log(Log.All, "f_count", f_count, "f_sp_count", f_sp_count)
            fine = 0.0
            ff_cnt = 0
            for f_cnt in range(min(f_count, f_sp_count)):
                if ff_cnt>=len(sp.fragments):
                    break
                partial_fine = self.fragments[f_cnt].compare_with(sp.fragments[ff_cnt])
                log.log(Log.All, partial_fine)
                if partial_fine["scale"]>2.0:
                    log.log(Log.Medium, "Scale to large, trying to merge 2 additional parts")
                    if ff_cnt+2>=len(sp.fragments):
                        break
                    partial_fine2 = self.fragments[f_cnt].compare_with(sp.fragments[ff_cnt:ff_cnt+3])
                    ff_cnt += 2
                    log.log(Log.All, partial_fine2)
                    partial_fine = partial_fine2
                scale_fine = 1.0
                if partial_fine["scale"]>1.0:
                    scale_fine = partial_fine["scale"]
                else:
                    scale_fine = 1.0/partial_fine["scale"]
                fine += partial_fine["diff"]*scale_fine
                ff_cnt += 1
            log.log(Log.All, "Per fragment fine", fine)
            fragment_fine = float(f_count-min(f_count, f_sp_count)) * fine/min(f_count, f_sp_count)
            return fine+fragment_fine
        except:
            log.log(Log.All,traceback.format_exc())
        
    def compare_flist(self, sp, options=None):
        try:
            cmp_opts = SigPattern.default_options
            try:
                cmp_opts["fine-for-scaling"] = options["fine-for-scaling"]
            except:
                pass
            try:
                cmp_opts["fine-for-inlinear-scaling"] = options["fine-for-inlinear-scaling"]
            except:
                pass
            try:
                cmp_opts["fine-for-uncompared"] = options["fine-for-uncompared"]
            except:
                pass
            
            
            fine_for_scaling = cmp_opts["fine-for-scaling"]
            fine_for_inlinear_scaling = cmp_opts["fine-for-inlinear-scaling"]
            fine_for_uncompared = cmp_opts["fine-for-uncompared"]
            
            f_count = len(self.fragment_list)
            f_sp_count = len(sp.fragment_list)
            fine = 0.0
            ff_cnt = 0
            scales = []
            for f_cnt in range(min(f_count, f_sp_count)):
                if ff_cnt>=len(sp.fragment_list):
                    break
                partial_fine = self.fragment_list[f_cnt].compare_with(sp.fragment_list[ff_cnt])
                
                if fine_for_scaling or fine_for_inlinear_scaling:
                    scales.append(partial_fine["scales"][0])
                    scale_fine = 0
                    if fine_for_scaling:
                        for s in partial_fine["scales"]:
                            if s>1.0:
                                scale_fine += s
                            else:
                                scale_fine += 1.0/s
                        fine += partial_fine["diff"]*scale_fine
                else:
                    fine += partial_fine["diff"]
                log.log(Log.All, partial_fine)
                ff_cnt+=1
            if fine_for_inlinear_scaling:
                inlinear_fine = numpy.std(scales)*fine
                fine += inlinear_fine
            if fine_for_uncompared:
                fragment_fine = float(f_count-min(f_count, f_sp_count)) * fine/min(f_count, f_sp_count)
                fine += fragment_fine
            return fine
        except:
            log.log(Log.All, traceback.format_exc())
    
    def filter_sig(self, filter_width):
        s = copy.deepcopy(self.sig)
        for i in range(len(self.sig)):
            l = max(i-filter_width/2,0)
            r = min(i+filter_width/2, len(self.sig)-1)
            s[i] = numpy.sum(self.sig[l:r])/float(len(self.sig[l:r]))
        self.sig = s
    
    def build_flist(self, flen):
        self.fragment_list = []
        for i in range(len(self.fragments)-flen):
            self.fragment_list.append(FragmentList(self.fragments[i:i+flen]))
    
    def build(self, filter_width=None):
        if None!=filter_width:
            self.filter_sig(filter_width)
        self.find_max()
        self.find_min()
        s_min = copy.deepcopy(self.s_min)
        s_max = copy.deepcopy(self.s_max)
        log.log(Log.All,  s_max)
        log.log(Log.All, s_min)
        if s_min[0] < s_max[0]:
            x = s_min[0]
            x_is_min = True
            s_min = s_min[1:]
        else:
            x = s_max[0]
            x_is_min = False
            s_max = s_max[1:]
        try:
            while len(s_max)>0 or len(s_min>0):
                if x_is_min:
                    xx = s_max[0]
                    s_max = s_max[1:]
                else:
                    xx = s_min[0]
                    s_min = s_min[1:]
                if x>=len(self.sig) or xx>=len(self.sig):
                    break
                if x>xx:
                    log.log(Log.Critical, "min max order corrupted")
                    break
                if x_is_min:
                    f_type = Fragment.min_to_max
                else:
                    f_type = Fragment.max_to_min
                f = Fragment(f_type, x, xx, self.sig)
                self.fragments.append(f)
                x = xx
                x_is_min = not x_is_min
        except:
            pass
        log.log(Log.All, "fragments count", len(self.fragments))
            
class MatrixPattern:
    def __init__(self, wavelet, root):#mtx, start_row, stop_row):
        #self.mtx = mtx
        self.rows = {}
        self.start_row = root.start_row()
        self.stop_row = root.stop_row()
        for i in range(self.start_row, self.stop_row):
            start_index = root.relative_offset_at_row(i)-2
            stop_index = start_index+350
            sp = SigPattern(wavelet[i,start_index:stop_index])
            sp.build()
            sp.build_flist(3)
            self.rows[i] = sp
    def compare_with(self, ptrn):
        start_row = max(self.start_row, ptrn.start_row)
        stop_row = min(self.stop_row, ptrn.stop_row)
        for i in range(start_row, stop_row):
            if len(self.rows[i].fragments)>2 and len(ptrn.rows[i].fragments)>2:
                print "Flist compare - Row", i, "Result", self.rows[i].compare_flist(ptrn.rows[i])
            else:
                print "List compare - Row", i , "Result", self.rows[i].compare(ptrn.rows[i])
    def save(self):
        with open("./temporary/pattern.pickle", "w") as f:
            pickle.dump(self, f)
            
class MatrixPatternLoader(folderscan.FolderScan):
    def __init__(self, path):
        self.patterns = []
        self.pattern_id = None
        
        folderscan.FolderScan.__init__(self, path)
    def on_folder_loaded(self):
        info_file = self.get_file("info")
        with open(info_file) as f:
            self.pattern_id = f.readline()
        pickled_patterns = self.get_files("*.pickle")
        for pp in pickled_patterns:
            with open(pp) as f:
                self.patterns.append(pickle.load(f))
    
    def create_subitem(self, path):
        return MatrixPatternLoader(path)
    
    def get_patterns(self):
        pl = []
        if len(self.patterns)>0:
            for p in self.patterns:
                pl.append([p, self.pattern_id])
            return pl
        for s in self.subitems.values():
            pll = s.get_patterns()
            for p in pll:
                p.append(self.pattern_id)
                pl.append(p)
        return pl

class SkeletonCompare:
    def __init__(self, manager, wavelet_src, root_src):
        self.man = manager
        self.wavelet_src = wavelet_src
        self.root_src = root_src
        #self.man.register_handler(wavelet_src, self.handle_wavelet)
        self.man.register_handler(root_src, self.handle_roots)
        self.man.add_data_id("matrix_compare", "matrix compare class")
        self.patterns = []
        
        mpl = MatrixPatternLoader('./temporary/patterns')
        self.patterns = mpl.get_patterns()
    def handle_wavelet(self, ticket):
        self.wavelet = ticket.get_data().get_wavelet()
    def handle_roots(self, ticket):
        root = ticket.get_data()
        try:
            wavelet = ticket.find_parent_by_data_id(self.wavelet_src).get_data().get_wavelet()
            print "Parsing root", ticket.description
            print root.start_row(), root.start_offset()
            mp = MatrixPattern(wavelet, root)
            self.man.push_ticket(ticket.create_ticket("matrix_compare", mp))
            self.compare_patterns(mp)
        except:
            print traceback.format_exc()
    def compare_patterns(self, ref_ptrn):
        for i in self.patterns:
            log.log(Log.Critical, "Comparing..."+str(i[1:]))
            ref_ptrn.compare_with(i[0])

if __name__ == "__main__" :
    src = numpy.loadtxt(u'./a_Дроздов.txt')
    src = src[:, 10:-10]
    src2 = numpy.loadtxt(u'./o_Дроздов.txt')
    src2 = src2[:, 10:-10]
    pyplot.figure()
    for r in range(src.shape[0]):
        pyplot.subplot(src.shape[0], 1, r+1)
        pyplot.plot(src[r,:])
    pyplot.show()
    
    exit(0)
    
    row = src[6,:]
    row2 = src[6,:]
    r1 = row[585:1000]
    #r2 = row2[1046:1440]
    r2 = src2[6, 640:1040]
    
    log.log(Log.All, "Fragments for r1")
    sp1 = SigPattern(r1)
    sp1.build()
    if log.details_level<Log.Medium:
        sp1.print_fragments()
    
    log.log(Log.All, "Fragments for r2")
    sp2 = SigPattern(r2)
    sp2.build()
    if log.details_level<Log.Medium:
        sp2.print_fragments()
    
    log.log(Log.Always, "Complete fine", sp1.compare(sp2))
    
    sp1.build_flist(3)
    sp2.build_flist(3)
    log.log(Log.Always, "Complete fine", sp1.compare_flist(sp2, {"fine-for-scaling":True, "fine-for-inlinear-scaling":True}))
    
    pyplot.subplot(2,1,1)
    pyplot.plot(sp1.sig)
    pyplot.subplot(2,1,2)
    pyplot.plot(sp2.sig)
    pyplot.show()
#6-575-1000
#6-1046-1440

def init_module(manager, gui):
    return [SkeletonCompare(manager, "wavelet" ,"skeleton-root-valid")]

