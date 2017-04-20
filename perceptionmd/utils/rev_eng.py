#!/usr/bin/python3
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import numpy as np
import six
import sys

if six.PY2:
    import itertools
    imap = itertools.imap

if six.PY3:
    xrange = range
    imap = map


def detect_shape(inputdata, dtype=np.float32, threeD=True):
    """
    This function tries to detect the shape of the array based on correlations.
    If the data is correlated, then there is a good chance for proper detection.
    Shape of uncorrelated data is unrecoverable, therefore the result will be gibberish.

    If the input is a string, then the function reads it as a binary array.

    The function returns the data in the detected shape.
    """
    import scipy.fftpack

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

    def getOffset(array, minium_data=3):
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

    if isinstance(inputdata, six.string_types):
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
    acc = sorted([(value, key) for (key, value) in acc.items()])
    a = acc[-1][1]

    acc = dict()
    idx2min = max(0, idx2 - W)
    idx2max = min(q.shape[0], idx2 + W + 1)

    for i in range(idx2min, idx2max):
        k = detect_shape(q[i, :]).shape
        acc[k] = acc.get(k, 0) + 1
    acc = sorted([(value, key) for (key, value) in acc.items()])
    b = acc[-1][1]

    shape = (-1,) + a + b
    data = np.squeeze(data.reshape(shape))
    if len(data.shape) == 2 and threeD:
        return data.reshape(-1, data.shape[1], data.shape[1])
    return data


def recognize_filetype(fn, default_type = np.float32, default_little_endian=True):
    """
    Recognize endianness and number format on raw file on the filename.
    Return value: (numpy.dtype, number==Little Endian?)

    >>> recognize_filetype("test_float_le.raw")
    (<type 'numpy.float32'>, True)

    >>> recognize_filetype("test_uint8_big_endian.raw")
    (<type 'numpy.uint8'>, False)

    >>> recognize_filetype("test.raw")
    (<type 'numpy.float32'>, True)

    """
    filename = fn.lower()
    LE = default_little_endian
    if filename.find("_le_") > -1: LE = True
    if filename.find("_little_") > -1: LE = True
    if filename.find("_little_endian_") > -1: LE = True
    if filename.find("_be_") > -1: LE = False
    if filename.find("_big_") > -1: LE = False
    if filename.find("_big_endian_") > -1: LE = False
    if filename.find("_mac_") > -1: LE = False

    if filename.find("_le.") > -1: LE = True
    if filename.find("_little.") > -1: LE = True
    if filename.find("_little_endian.") > -1: LE = True
    if filename.find("_be.") > -1: LE = False
    if filename.find("_big.") > -1: LE = False
    if filename.find("_big_endian.") > -1: LE = False
    if filename.find("_mac.") > -1: LE = False

    if filename.find("_float_") > -1: return np.float32, LE
    if filename.find("float32") > -1: return np.float32, LE
    if filename.find("float64") > -1: return np.float64, LE
    if filename.find("double") > -1: return np.float64, LE
    if filename.find("uint8") > -1: return np.uint8, LE
    if filename.find("uint16") > -1: return np.uint16, LE
    if filename.find("uint32") > -1: return np.uint32, LE
    if filename.find("uint64") > -1: return np.uint64, LE
    if filename.find("uint") > -1: return np.uint32, LE
    if filename.find("ushort") > -1: return np.uint16, LE
    if filename.find("ulong") > -1: return np.uint64, LE

    if filename.find("int8") > -1: return np.int8, LE
    if filename.find("int16") > -1: return np.int16, LE
    if filename.find("int32") > -1: return np.int32, LE
    if filename.find("int64") > -1: return np.int64, LE
    if filename.find("int") > -1: return np.int32, LE
    if filename.find("short") > -1: return np.int16, LE
    if filename.find("long") > -1: return np.int64, LE

    return default_type, LE


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

    candidates = sorted([(v, k) for k, v in mean.items()])
    return np.dtype(candidates[0][1])

if __name__ == "__main__":
    import doctest
    doctest.testmod()
    t=detect_filetype(sys.argv[1])
    print(t,detect_shape(sys.argv[1],dtype=t).shape)

