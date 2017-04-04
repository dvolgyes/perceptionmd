#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

import numpy as np
import os
import dicom
from . import VolumeReader
import collections


def at_least_3d(array):
    if len(array.shape) == 1:
        return array.reshape(1, 1, -1)
    if len(array.shape) == 2:
        return array.reshape((-1,) + array.shape)
    return array


class DICOMDIR(VolumeReader.VolumeReader):

    def __init__(self, *args, **kwargs):
        super(DICOMDIR, self).__init__(*args, **kwargs)
        self.filename_cache = collections.defaultdict(list)

    def volume_iterator(self, dirname):
        volnames = []
        for root, dirnames, filenames in os.walk(dirname, followlinks=True):
            for f in filenames:
                p = os.path.join(root, f)
                try:
                    ds = dicom.read_file(p)
                    series = ds.SeriesInstanceUID
                    self.filename_cache[series].append(p)
                    self.UID2dir_cache[series] = root
                    volnames.append((series, root))
                except:
                    continue
        for volname, root in sorted(list(set(volnames)), key=lambda x: x[1]):
            yield volname

    def volume(self, UID):
        with self.lock:
            if UID in self.cache and self.cache[UID] is not None:
                return self.cache[UID]
            if len(self.filename_cache[UID]) == 1:
                ds = dicom.read_file(self.filename_cache[UID][0])
                if ('RescaleIntercept' in ds) and ('RescaleSlope' in ds):
                    intercept = ds.RescaleIntercept
                    slope = ds.RescaleSlope
                else:
                    slope, intercept = 1, 0
                volume = ds.pixel_array.copy().astype(self.dtype) * slope + intercept
            else:
                zpos = []
                for f in self.filename_cache[UID]:
                    ds = dicom.read_file(f)
                    z = ds.SliceLocation
                    if ('RescaleIntercept' in ds) and ('RescaleSlope' in ds):
                        intercept = ds.RescaleIntercept
                        slope = ds.RescaleSlope
                    else:
                        slope, intercept = 1, 0
                    vol = ds.pixel_array.copy().astype(self.dtype) * slope + intercept
                    zpos.append((z, vol))
                zpos = sorted(zpos, key=lambda x: x[0])
                _, volumes = zip(*zpos)
                volume = np.stack(volumes)
            self.cache[UID] = volume
        return at_least_3d(volume)
