#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division

from perceptionmd.utils import gc_after
import threading
import numpy as np

from abc import abstractmethod
import cachetools
from collections import defaultdict

class VolumeReader(object):

    def __init__(self, lock=threading.Lock(),cache=cachetools.LRUCache(maxsize=1), dtype=np.float32, shape='auto', *args, **kwargs):
        self.dtype = dtype
        self.volume_shapes = dict()
        self.volume_types = dict()
        self.cache = cache
        self.lock = lock
        self.threads = list()
        self.pixelsize = (1., 1., 1.)
        self.UID2dir_cache = defaultdict(str)

    def get_pixelsize(self):
        return self.pixelsize


    def UID2dir(self,UID):
        return self.UID2dir_cache[UID]

    @gc_after
    def cleanup(self):
        result = []
        with self.lock:
            for thread in self.threads:
                if thread.is_alive():
                    result.append(thread)
        self.threads = result

    def set_cache(self, cache):
        self.cache = cache

    def preload_volume(self, UID):
        print("background thread started")
        with self.lock:
            caching_thread = threading.Thread(target=self.volume, args=(UID,))
            self.threads.append(caching_thread)
        caching_thread.start()

    @abstractmethod
    def volume_iterator(self, directory):
        pass

    @abstractmethod
    def volume(self, UID):
        pass