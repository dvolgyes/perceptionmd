#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division

import numpy as np
import os
import dicom
from operator import itemgetter,attrgetter
import threading
import gc
from cachetools import cachedmethod, LRUCache, RRCache

import numpy as np
import scipy.fftpack
import sys
import six
import re

if six.PY2:
    import itertools
    imap = itertools.imap

if six.PY3:
    xrange = range
    imap = map

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


def detect_shape(inputdata, dtype=np.float32):
    """
    This function tries to detect the shape of the array based on correlations.
    If the data is correlated, then there is a good chance for proper detection.
    Shape of uncorrelated data is unrecoverable, therefore the result will be gibberish.

    If the input is a string, then the function reads it as a binary array.

    The function returns the data in the detected shape.
    """

    def divisors(n, trivial=False):
        large = []
        small = []
        if trivial:
            for i in xrange(1, int(np.sqrt(n) + 1)):
                if n % i == 0:
                    small.append(i)
                    if i * i != n:
                        large.append(n / i)
        else:
            for i in xrange(2, int(np.sqrt(n) + 1)):
                if n % i == 0:
                    small.append(i)
                    if i * i != n:
                        large.append(int(n / i))
        return small + large[::-1]

    def getOffset(array, minium_data=100):
        if array.size < minium_data:
            return 1

        divs = divisors(array.size, trivial=False)

        if len(divs) == 2:
            return 1

        a = array.ravel()

        lf2 = np.power(scipy.fftpack.rfft(a), 2.0)
        linv = scipy.fftpack.irfft(lf2)
        n = 1
        for i in divs:
            if i == 0 or i == 1:
                continue
            if linv[i] > linv[n]:
                n = i
        return n

    if type(inputdata) == str:
        data = np.fromfile(inputdata, dtype=dtype)
    else:
        data = inputdata

    if data.size <= 1:
        return data

    if data.dtype.byteorder != "=":
        data = data.astype(data.dtype.newbyteorder("="))
    if data.dtype == np.float16:
        data = data.astype(np.float32)

    n1 = getOffset(data)
    q = data.reshape(-1, n1)
    s = np.sum(q, axis=0)
    s2 = np.sum(q, axis=1)

    idx1 = np.argmax(s)
    idx2 = np.argmax(s2)

    if n1 == 1:
        return data

    W = 2

    acc = dict()
    idx1min = max(0, idx1 - W)
    idx1max = min(q.shape[1], idx1 + W + 1)

    for i in range(idx1min, idx1max):
        k = detect_shape(q[:, i]).shape
        acc[k] = acc.get(k, 0) + 1
    acc = list([(value, key) for (key, value) in acc.items()])
    acc.sort()
    a = acc[-1][1]

    acc = dict()
    idx2min = max(0, idx2 - W)
    idx2max = min(q.shape[0], idx2 + W + 1)

    for i in range(idx2min, idx2max):
        k = detect_shape(q[i, :]).shape
        acc[k] = acc.get(k, 0) + 1
    acc = list([(value, key) for (key, value) in acc.items()])
    acc.sort()
    b = acc[-1][1]

    shape = (-1,) + a + b
    return np.squeeze(data.reshape(shape))


def detect_filetype(filename, offset=0, types='all', endian='all', count=-1):
    """
    This function tries to detect the number format in a raw file.
    There are several assumptions, the detection is not always correct.
    The most important assumptions are:
      - NaN,inf,-inf are not present in the data
      - extreme values are unlikely
    """
    dbuffer = np.memmap(filename, mode="r", offset=offset, dtype=np.int8)

    filesize = dbuffer.size

    if types == 'float':
        typelist = ['f4', 'f8', 'f2']
    elif types == 'integer':
        typelist = ['i4', 'u4']
    else:
        typelist = ['f4', 'f8', 'f2', 'i4', 'u4']

    if endian == 'big':
        endianlist = ['>']
    elif endian == 'little':
        endianlist = ['<', ]
    else:
        endianlist = ['<', '>']

    mean = dict()

    for t in typelist:
        for e in endianlist:
            dtype = np.dtype(e + t)
            if filesize % dtype.itemsize != 0:
                continue

            tc = min(count, filesize // dtype.itemsize)

            array = np.frombuffer(dbuffer, count=tc, dtype=dtype)
            with np.errstate(invalid='ignore'):
                if not all(imap(np.isfinite, array.flat)):
                    continue
            m = np.abs(np.mean(array))

            if np.isnan(m) or not np.isfinite(m):
                continue
            if t == 'f4' and (m < 1e-25 or m > 1e+25):
                continue
            if t == 'f2' and (m < 5e-5 or m > 65000):
                continue
            if t == 'f8' and (m < 1e-200 or m > 1e+200):
                continue

            mean[dtype] = m

    candidates = [(v, k) for k, v in mean.items()]
    candidates.sort()
    return np.dtype(candidates[0][1])

class RAWDIR():

    def __init__(self,dirname,dtype=np.float32,shape='auto',*args,**kwargs):
        self.directory = dirname
        self.dtype = dtype
        self.volume_shapes = dict()
        self.volume_types = dict()

    def infer_shape(self,filename,dtype='auto'):
        shape_regexp = re.compile(r"\D+(\d+)\D+(\d+)\D+(\d+)\D*.raw",flags=re.IGNORECASE)
        result = shape_regexp.match(filename)
        if result:
            z,y,x = result.group(1,2,3)
            z,y,x = int(z),int(y),int(x)
            return (z,y,x)
        if dtype == 'auto':
            dtype = detect_filetype(filename)
        return detect_shape(filename, dtype=dtype).shape

    def volume_iterator(self,dirname=None):
        if dirname is None:
            dirname = self.directory
        for fn in sorted(scandir(dirname)):
            if fn.name.lower().endswith("raw"):
               yield os.path.join(dirname,fn.name)

    def volume(self,filename,dtype=None,shape='auto'):
        if filename not in self.volume_types:
            if self.dtype is None and self.dtype is None:
                dtype = detect_filetype(filename)
            else:
                dtype = self.dtype
        else:
            dtype = self.volumes_types[filename]
            self.volume_types[filename] = dtype

        shape = self.volume_shapes.get(filename,'auto')
        if shape=='auto':
            shape = self.infer_shape(filename, dtype)
            self.volume_shapes[filename] = shape
        print(os.getcwd(),filename,dtype)
        return np.memmap(filename, mode="r", offset=0, dtype=dtype).reshape(shape)

if __name__ == "__main__":
    rawdir = RAWDIR(sys.argv[1])
    for vol in rawdir.volume_iterator():
        print(vol)
        print(rawdir.infer_shape(vol,np.float32))
    #~ dt = detect_filetype(filename, count=10000)
    #~ print("Filename: %s     detected type: %s " % (filename, dt))
    #~ print(detect_shape(filename, dtype=dt).shape)

