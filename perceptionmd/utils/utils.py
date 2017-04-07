#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

import gc as garbage_collector
from contextlib import contextmanager
from functools import wraps
import importlib
import itertools
import random
import numpy as np
import shutil
import tempfile
import os


def listify(arg):
    if arg is None:
        return list()
    if hasattr(arg, '__iter__'):
        return arg
    return list((arg,))


def KV(kvs, key):
    for kv in kvs:
        if kv.key == key:
            return kv.value
    return None


def random_combinations(lst, count=2):
    result = []
    comb = list(itertools.combinations(lst, count))
    random.shuffle(comb)
    for c in comb:
        v = c if random.randint(0, 1) == 0 else c[::-1]
        result.append(v)
    return result


def padding(array, shape):
    result = []
    for i in range(len(shape)):
        d = shape[i] - array.shape[i]
        result.append((d // 2, d - d // 2))
    return np.pad(array, tuple(result), mode='constant')


def padding_square(array):
    largest_dimsize = max(array.shape)
    return padding(array, (largest_dimsize,) * len(array.shape))


def test_module(name):
    """
    Test if module is importable.
    """
    try:
        importlib.import_module(name)
        return True
    except:
        return False


def test_feature(module, name):
    try:
        importlib.import_module(name)
        return True
    except:
        return False

try:
    scandir = os.scandir

except AttributeError:
    try:
        import scandir
        scandir = scandir.scandir
    except ImportError:
        def scandir(dirname="."):
            for root, dirs, files in os.walk(dirname):
                for f in files:
                    yield os.path.join(root, f)


def gc(func):
    """
    Unconditional garbage collection decorator,
    which perform garbage collection before and after
    the execution of the function.
    """
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        garbage_collector.collect()
        result = func(*args, **kwargs)
        garbage_collector.collect()
        return result
    return func_wrapper


def gc_before(func):
    """
    Unconditional garbage collector decorator,
    executing garbage collection before the function call.
    """
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        garbage_collector.collect()
        return func(*args, **kwargs)
    return func_wrapper


def gc_after(func):
    """
    Unconditional garbage collector decorator,
    executing garbage collection after the function call.
    """
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        garbage_collector.collect()
        return result
    return func_wrapper


@contextmanager
def gc_ctx():
    """
    Garbage collection context manager:
    executing garbage collection before and after the function call.
    """
    garbage_collector.collect()
    yield
    garbage_collector.collect()


@contextmanager
def gc_ctx_before():
    """
    Garbage collection context manager:
    executing garbage collection before and after the function call.
    """
    garbage_collector.collect()
    yield


@contextmanager
def gc_ctx_after():
    """
    Garbage collection context manager:
    executing garbage collection before and after the function call.
    """
    yield
    garbage_collector.collect()


@contextmanager
def tmpdir_ctx():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


@contextmanager
def delete_file_ctx(f):
    yield
    if isinstance(f, file):
        name = f.name
        if not f.closed:
            f.close()
        os.remove(name)
    else:
        os.remove(f)


@contextmanager
def tmpfile_ctx():
    tmpfile = tempfile.mkstemp()
    with open(tmpfile[1], "wb+") as f:
        yield f
    os.remove(tmpfile[1])

if __name__ == "__main__":
    @gc
    def test_gc():
        with gc_ctx():
            return None

    @gc_before
    def test_gc_before():
        with gc_ctx_before():
            return None

    @gc_after
    def test_gc_after():
        with gc_ctx_after():
            return None

    with gc_ctx_after():
        print("test")
    test_gc_before()
    test_gc_after()
    test_gc()
