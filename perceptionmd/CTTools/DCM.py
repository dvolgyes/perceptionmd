
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division

import numpy as np
import os
import dicom
from operator import itemgetter,attrgetter
import threading
import gc
from cachetools import cachedmethod, LRUCache, RRCache

try:
    from os import scandir, walk
except ImportError:
    try:
        from scandir import scandir, walk
    except:
        from os import walk
        def scandir(dirname="."):
            for root,dirs,files in os.walk(dirname):
                for f in files:
                    yield os.path.join(root,f)


def tostr(x):
    if isinstance(x,bytes):
        return x.decode(encoding='UTF-8')
    return x

def repuid(obj):
    return rep(obj).replace("_", "")


def rep(obj):
    result = ""
    if isinstance(obj,bytes):
        return tostr(obj)
    if type(obj) != str:
        try:
            for o in obj:
                result += str(o) + " "
        except:
            result = str(obj)
    else:
        result = str(obj)
    return result.strip().replace(" ", "_")


class DCM(object):

    def __init__(self, dirname=None,*args,**kwargs):
        self.volume = None
        self.dcms = []
        self.pixelsize = {'z': 0.0, 'y': 0.0, 'x': 0.0}
        self.selected_idx = 0
        self.positions = []
        self.minpos = 0
        self.maxpos = 0

        if dirname:
            self.read_volumes(dirname)

    def __getattr__(self, name):
        try:
            return getattr(self, name)
        except:
            return getattr(self.dcms[self.selected_idx], name)
        return None

    def select(self, idx):
        ridx = int(np.around(idx))
        self.selected_idx = ridx
        ridx = np.clip(ridx, 0, self.volume.shape[0] - 1)
        self.image = self.volume[ridx, :, :]
        return self.image

    def select_by_pos(self, pos):
        idx = np.argmin(np.abs(self.positions - pos))
        return self.select(idx)

    def SeriesUIDs(self, dirname):
        UIDs = dict()
        if not os.path.exists(dirname) or not os.path.isdir(dirname):
            return None

        for f in sorted(scandir(dirname)):
            image, ds = self.__read_dcm(os.path.join(dirname, f.name))
            if image is None: continue
            if ds is not None:
                try:
                    UID = str(ds.SeriesInstanceUID)+str(ds.SeriesNumber)
                    UIDs[UID] = ds
                except:
                    pass
        return UIDs

    def __read_dcm(self, filename, ntype=np.float32, rot = 0):
        image,ds = None,None
        ds = dicom.read_file(filename)
#        print(len(self.cache._data))
        orient = list(map(int,map(float,(ds[0x0020,0x0037]))))
        intercept = ds.RescaleIntercept
        slope = ds.RescaleSlope
        image = ds.pixel_array.copy().astype(ntype)

        if image is not None:
            if rot > 0:
                image = np.rot90(image,rot)
            image = image * slope + intercept
        return (image, ds)

    def read_volumes(self,
                     dirname,
                     skiplist=['png', 'txt', 'tex'],
                     UIDs=None,
                     ntype=np.float32):

        def dicomcomparator(x, y):
            p1 = x[1].SliceLocation
            p2 = y[1].SliceLocation
            return int(float(p1) - float(p2))

        if not os.path.exists(dirname) or not os.path.isdir(dirname):
            return None

        result = []

        for f in sorted(scandir(dirname)):
            try:
                name = f.name
            except:
                name = f
            if f.name.endswith(".png"):
                continue
            if f.name.endswith(".txt"):
                continue
            if f.name.endswith(".tex"):
                continue
            if f.name.endswith("DIRFILE"):
                continue
            if f.name.endswith("DCMDIR"):
                continue

            image, ds = self.__read_dcm(os.path.join(dirname, f))
            if image is None: continue
            if image is not None and (UIDs is None or ds.SeriesInstanceUID in UIDs):
                result.append((image, ds))
        z, y, x = len(result), 0, 0
        if z == 0:
            return None
        (x, y) = result[0][0].shape

        self.volume = np.zeros((z, y, x), dtype=ntype)
        self.positions = np.zeros((z,), dtype=np.float32)
        self.dcms = []
        result.sort(dicomcomparator)
        for idx in range(z):
            self.volume[idx, :, :] = result[idx][0]
            self.dcms.append(result[idx][1])
            self.positions[idx] = self.dcms[-1].SliceLocation
        self.minpos, self.maxpos = np.amin(
            self.positions), np.amax(self.positions)

    def read_from_files(self,
                     filelist,
                     skiplist=['png', 'txt', 'tex'],
                     UIDs=None,
                     ntype=np.float32,rot=0):

        def dicomcomparator(x, y):
            p1 = x[1].SliceLocation
            p2 = y[1].SliceLocation
            return int(float(p1) - float(p2))

        def dicomkey(x):
            p1 = x[1].SliceLocation
            return float(p1)


        result = []
        for no,f in sorted(filelist):
            if f.endswith(".png"):
                continue
            if f.endswith(".txt"):
                continue
            if f.endswith(".tex"):
                continue
            image, ds = self.__read_dcm(os.path.join(f))
            if image is None: continue
            if image is not None and (UIDs is None or ds.SeriesInstanceUID in UIDs):
                result.append((image, ds))
        z, y, x = len(result), 0, 0
        if z == 0:
            return None
        (x, y) = result[0][0].shape

        self.volume = np.zeros((z, y, x), dtype=ntype)
        self.positions = np.zeros((z,), dtype=np.float32)
        self.dcms = []
        try:
            result.sort(cmp=dicomcomparator)
        except:
            result.sort(key=dicomkey)

        for idx in range(z):
            if rot > 0:
                self.volume[idx, :, :] = np.rot90(result[idx][0],rot)
            else:
                self.volume[idx, :, :] = result[idx][0]
            self.dcms.append(result[idx][1])
            self.positions[idx] = self.dcms[-1].SliceLocation
        self.minpos, self.maxpos = np.amin(
            self.positions), np.amax(self.positions)
        return self.volume

class DICOMDIR(object):

    def __init__(self, *args, **kwargs):
        self._details = dict()
        self._instance = dict()
        self._slices = dict()
        self._files = dict()
        self._descriptions = dict()
        self._texts = dict()
        self._sorter = dict()
        self.lock = threading.Lock()
        self.cache = kwargs.get('cache',RRCache(maxsize=6))
        self.lock = threading.Lock()
        self.threads = dict()

    def reset(self, *args, **kwargs):
        self._details.clear()
        self._instance.clear()
        self._slices.clear()

    def scan_dirs(self, *args, **kwargs):
        sort = True
        try:
            sort = bool(kwargs['sorted'])
        except:
            pass
        if sort:
            for x in sorted(self._scan_dirs(*args)):
                yield x
        else:
            for x in self._scan_dirs(*args):
                yield x

    def find_dicoms(self, *args):
        files = self.scan_dirs(*args, sorted=True)
        for f in files:
            ds = dicom.read_file(f)
            try:
                if str(ds.SOPClassUID)!="CT Image Storage": continue
            except:
                continue
            if 'LOCALIZER' in ds.ImageType: continue
            if 'SCREEN SAVE' in ds.ImageType: continue
            series = str(ds.SeriesInstanceUID)+str(ds.SeriesNumber)
            try:
                orient = list(map(int,map(float,(ds[0x0020,0x0037]))))
                if orient==[0, 1, 0, 0, 0, -1]: continue
            except:
                continue
            #~ print(orient,ds.SliceThickness)
            try:
                location = float(ds.SliceLocation)
                #~ print(ds.ImageType)
            except:
                #~ print("no position",ds.ImageType,f)
                #~ print(ds.ImageType)
                continue
                #~ sys.exit(1)
            if series not in self._descriptions:
                manufacturer = rep(ds.Manufacturer)
                kernel = rep(ds.ConvolutionKernel)
                try:
                    filter = rep(ds.FilterType)
                except:
                    filter = ""

                algorithm="NA"
                strength="NA"
                study = repuid(ds.StudyInstanceUID)
                thickness = float(rep(ds.SliceThickness))
                try:
                    sdesc = rep(ds.SeriesDescription).replace(",",".")
                except:
                    sdesc = ""
                seriesnumber = "%02i" % int(str(ds.SeriesNumber))

                if manufacturer.startswith("TO"):
                    manufacturer = "TO"
                    try:
                        af=rep(ds[0x7005,0x1021].value)
                        if af.startswith("BOOST"):
                            algorithm = "QDS"
                            strength = "BOOST"
                    except:
                        pass
                    try:
                        af=rep(ds[0x7005,0x100b].value)
                        if af.startswith("AIDR"):
                            algorithm = af.strip()
                            strength = "STD"
                    except:
                        pass

                if manufacturer.startswith("GE"):
                    algorithm = "NA"
                    manufacturer = "GE"
                    if (0x0018,0x1020) not in ds:
                        try:
                            strength = 0
                            algorithm = "ASIR"
                            ir=rep(ds[0x0053,0x1043].value)
                            strength = ir
                        except:
                            pass
                    else:
                        try:
                            algorithm = "VEO"
                            strength = "0" # str(ds.FilterType)
                        except:
                            strength="ERROR"

                if manufacturer.startswith("Phi"):
                    manufacturer = "PH"
                    kernels = kernel.split(",")
                    if len(kernels) == 1:
                        algorithm = "iDose"
                        if len(sdesc)>6:
                            strength = sdesc[6]
                        else:
                            strength = "0"
                    else:
                        kernel,strength= kernel[0:3],kernel[3:4]
                        algorithm = kernels[1]


                if manufacturer.startswith("SIEM"):
                    manufacturer = "SI"
                    if kernel.startswith("B"):
                        algorithm="FBP"
                        strength="0"
                    else:
                        kernel = rep(ds.ConvolutionKernel[0])
                        algorithm = "SAFIRE"
                        strength = rep(ds.ConvolutionKernel[1])

                current = rep(ds.XRayTubeCurrent)
                pixels = list(map(float, ds.PixelSpacing)) + [thickness, ]
                try:
                    CTDI = "%.1f" % float(rep(ds.CTDIvol))
                except:
                    CTDI = "%s" % current
                KVP = rep(ds.KVP)
                self._descriptions[series] = (study, series, seriesnumber,manufacturer, KVP, thickness, sdesc, filter, kernel, current, pixels,algorithm,strength,CTDI)
                    #SERIESNUMBER MA S/L , 2.5/5.0/10. ,
                self._texts[series] = "%s,%s,%s,%s,%s,%s,%s" % (manufacturer, seriesnumber, CTDI, kernel, algorithm,strength, sdesc)

                self._details[series] = ds
                try:
                    strength = int(strength)
                except:
                    pass
                try:
                    CTDI = float(CTDI)
                except:
                    pass

                self._sorter[series] = (manufacturer,CTDI,kernel,algorithm,strength)
            if series not in self._files:
                self._files[series] = []
            self._slices[series] = (
                self._slices[series] + 1) if (series in self._slices) else 1
            self._files[series].append((location, f))


    def sort(self):
        for series in self.series_iterator():
            self._files[series].sort()

    def series_iterator(self):
        x = set([x for x in self._descriptions.keys()])
        results = []
        for s in x:
            results.append( (self._sorter[s])+(s,) )

        out = []
        for r in sorted(results, key=itemgetter(0,2,3,4,1)):
            s=r[-1]
            out.append(s)
        return out

    def pixelsize(self,series):
        z = float(rep(self._details[series].SliceThickness))
        (y,x) = map(float, self._details[series].PixelSpacing)
        return (z,y,x)

    def file_iterator(self,series):
            for (loc,filename) in sorted(self._files[series]):
                yield loc,filename

    def volume(self, UID,rot=2):
        with self.lock:
            if (UID,rot) in self.cache:
                return self.cache[(UID,rot)]
            vol = DCM().read_from_files(self._files[UID],rot=rot)
            self.cache[(UID,rot)] = vol
        return vol

    def preload_volumes(self,UID):
        with self.lock:
            self.threads.append(caching_thread)
            caching_thread = threading.Thread(target=self.volume,args=(UID,))
        caching_thread.start()

    def cleanup(self):
        result = []
        with self.lock:
            for thread in self.threads:
                if thread.is_alive():
                    result.append(thread)
        self.threads = result
        gc.collect()

    def _scan_dirs(self, *args):
        for arg in args:
            if type(arg) != str and hasattr(arg, '__iter__'):
                for a in arg:
                    for x in self.scan_dirs(a):
                        yield x
            else:
                for root, dirname, filename in walk(arg,followlinks=True):
                    for f in filename:
                        yield (os.path.join(root, f))


if __name__ == "__main__":
    print("test should run here")
