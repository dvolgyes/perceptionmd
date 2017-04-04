#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

import os
import re
import numpy as np

from . import VolumeReader
from perceptionmd.utils import detect_shape, detect_filetype, scandir


class RAWDIR(VolumeReader.VolumeReader):

    def __init__(self, dirname, shape='auto', *args, **kwargs):
        super(RAWDIR, self).__init__(*args, **kwargs)
        self.directory = dirname

    def infer_shape(self, filename, dtype='auto'):

        shape_regexp = re.compile(
            r"\D+(\d+)\D+(\d+)\D+(\d+)\D*.raw", flags=re.IGNORECASE)
        result = shape_regexp.match(os.path.split(filename)[1])
        if result:
            z, y, x = result.group(1, 2, 3)
            z, y, x = int(z), int(y), int(x)
            return (z, y, x)
        if repr(dtype) == 'auto':
            dtype = detect_filetype(filename)
        return detect_shape(filename, dtype=dtype).shape

    def volume_iterator(self, dirname=None):
        if dirname is None:
            dirname = self.directory

        for fn in sorted(scandir(dirname), key=lambda x: x.name):
            if fn.name.lower().endswith("raw"):
                root = os.path.split(fn.name)
                self.UID2dir_cache[dirname] = root
                yield os.path.join(dirname, fn.name)

    def volume(self, filename, dtype=None, shape='auto'):
        if filename not in self.volume_types:
            if self.dtype is None and self.dtype is None:
                dtype = detect_filetype(filename)
            else:
                dtype = self.dtype
        else:
            dtype = self.volumes_types[filename]
            self.volume_types[filename] = dtype

        shape = self.volume_shapes.get(filename, 'auto')
        if shape == 'auto':
            shape = self.infer_shape(filename, dtype)
            self.volume_shapes[filename] = shape
        return np.memmap(filename, mode="r", offset=0, dtype=dtype).reshape(shape)
