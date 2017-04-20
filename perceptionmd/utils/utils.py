#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import gc as garbage_collector
from contextlib import contextmanager
from functools import wraps
import importlib
import itertools
import numpy as np
import shutil
import tempfile
import os
import six
from collections import namedtuple

"""
This is a utility module with various, small functions and contexes
which did not fit elsewhere at this time. Any function here
might be relocated soon.
"""


def at_least_3d(array):
    """
    Returns the numpy array and reshapes it to have at least 3 dimensions.
    Extra dimensions are introduced at the front.

    >>> if True:
    ...     import numpy as np
    ...     print(at_least_3d(np.arange(6)).shape)
    (1, 1, 6)

    >>> if True:
    ...     import numpy as np
    ...     print(at_least_3d(np.arange(6).reshape(2,3)).shape)
    (1, 2, 3)

    >>> if True:
    ...     import numpy as np
    ...     print(at_least_3d(np.arange(6).reshape(3,1,2)).shape)
    (3, 1, 2)
    """
    if len(array.shape) == 1:
        return array.reshape(1, 1, -1)
    if len(array.shape) == 2:
        return array.reshape((-1,) + array.shape)
    return array


def listify(*arg):
    """
    Return the argument as a list, if it wasn't already a list.

    >>> listify(None)
    []
    >>> listify()
    []
    >>> listify(1)
    [1]
    >>> listify(1,2,3)
    [1, 2, 3]
    >>> listify([1,2,3])
    [1, 2, 3]
    >>> listify((1,2,3))
    [1, 2, 3]
    >>> listify('test')
    ['test']
    """
    if len(arg) == 0:
        return list()
    if len(arg) > 1:
        return list(arg)
    arg = arg[0]
    if arg is None:
        return list()
    if isinstance(arg, six.string_types):
        return list((arg,))
    if hasattr(arg, '__iter__'):
        return list(arg)
    return list((arg,))


def KV(kvs, key):
    """
    This is a test function

    >>> if True:
    ...    import collections
    ...    keyvalue=collections.namedtuple("keyvalue",["key","value"])
    ...    kvlist=[keyvalue(1,2),keyvalue(2,3)]
    ...    print(KV(kvlist,1))
    2

    >>> if True:
    ...    import collections
    ...    keyvalue=collections.namedtuple("keyvalue",["key","value"])
    ...    kvlist=[keyvalue(1,2),keyvalue(2,3)]
    ...    print(KV(kvlist,3))
    None

    """
    "Extracting value from a obj list with key and value parameters."
    for kv in kvs:
        if kv.key == key:
            return kv.value
    return None


def random_combinations(lst, count=2):
    """
    This is a test function

    >>> if True:
    ...    import numpy as np
    ...    np.random.seed(5)
    ...    print(random_combinations( [1,2,3] ))
    [(2, 1), (1, 3), (2, 3)]

    >>> if True:
    ...    import numpy as np
    ...    np.random.seed(5)
    ...    print(random_combinations( [1,2,3],3 ))
    [(3, 2, 1)]
    """

    result = []
    comb = list(itertools.combinations(lst, count))
    np.random.shuffle(comb)
    for c in comb:
        v = c if np.random.randint(2) == 0 else c[::-1]
        result.append(v)
    return result


def padding(array, shape):
    """
    Padding a numpy array with zeros to fit a given shape.
    If the padding isn't symmetric, then the bottom-right area
    should be larger.

    >>> if True:
    ...    import numpy as np
    ...    a = np.ones(shape=(1,1),dtype=np.uint8)
    ...    print(padding(a,(2,2)))
    [[1 0]
     [0 0]]

    >>> if True:
    ...    import numpy as np
    ...    a = np.ones(shape=(1,1),dtype=np.uint8)
    ...    print(padding(a,(3,3)))
    [[0 0 0]
     [0 1 0]
     [0 0 0]]


    """
    result = []
    for i in range(len(shape)):
        d = shape[i] - array.shape[i]
        result.append((d // 2, d - d // 2))
    return np.pad(array, tuple(result), mode='constant')


def padding_square(array):
    """Padding a numpy array with zeros to get square shaped arrangement.
    Always the smaller dimension is padded.

    >>> if True:
    ...    import numpy as np
    ...    a = np.arange(6).reshape(2,3)
    ...    print(padding_square(a))
    [[0 1 2]
     [3 4 5]
     [0 0 0]]

    """

    largest_dimsize = max(array.shape)
    return padding(array, (largest_dimsize,) * len(array.shape))


def test_module(name):
    """
    Test if module is importable.

    >>> test_module('os')
    True

    >>> test_module('non_existing_module')
    False
    """
    try:
        importlib.import_module(name)
        return True
    except:
        return False


def test_feature(module, name):
    """Test if module has a specific function or not
    >>> test_feature('os','walk')
    True
    >>> test_feature('os','non_existinging_function')
    False
    >>> test_feature('nonexisting_module','non_existinging_function')
    False

    """
    try:
        x = importlib.import_module(module, 'test_feature_dummy_import_module')
        return name in x.__dict__
    except:
        return False

def gc(func):
    """
    Unconditional garbage collection decorator,
    which perform garbage collection before and after
    the execution of the function.

    >>> if True:
    ...     @gc
    ...     def test_function(x):
    ...         return x
    ...     test_function(123)
    123
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

    >>> if True:
    ...     @gc_before
    ...     def test_function(x):
    ...         return x
    ...     test_function(123)
    123
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

    >>> if True:
    ...     @gc_after
    ...     def test_function(x):
    ...         return x
    ...     test_function(123)
    123

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

    >>> with gc_ctx():
    ...     print(123)
    123
    """
    garbage_collector.collect()
    yield
    garbage_collector.collect()


@contextmanager
def gc_ctx_before():
    """
    Garbage collection context manager:
    executing garbage collection before and after the function call.

    >>> with gc_ctx_before():
    ...     print(123)
    123

    """
    garbage_collector.collect()
    yield


@contextmanager
def gc_ctx_after():
    """
    Garbage collection context manager:
    executing garbage collection before and after the function call.

    >>> with gc_ctx_after():
    ...     print(123)
    123
    """

    yield
    garbage_collector.collect()


@contextmanager
def tmpdir_ctx():
    """
    >>> with tmpdir_ctx() as tmp:
    ...     import os
    ...     print(os.path.exists(tmp))
    True
    """

    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


@contextmanager
def delete_file_ctx(f):
    """
    Delete a given file after the context.
    For temporary files, you should rather consider to use tmpfile_ctx.

    >>> if True:
    ...     import tempfile
    ...     fn = tempfile.mkstemp()[1]
    ...     with delete_file_ctx(fn):
    ...         print(os.path.exists(fn))
    ...     print(os.path.exists(fn))
    True
    False

    >>> if True:
    ...     import tempfile
    ...     fn = tempfile.mkstemp()[1]
    ...     f = open(fn)
    ...     with delete_file_ctx(f):
    ...         print(os.path.exists(f.name))
    ...     print(os.path.exists(f.name))
    True
    False

    >>> if True:
    ...     import tempfile
    ...     fn = tempfile.mkstemp()[1]
    ...     f = open(fn)
    ...     with delete_file_ctx(f):
    ...         f.close()
    ...         print(os.path.exists(f.name))
    ...     print(os.path.exists(f.name))
    True
    False


    """
    yield
    if isinstance(f, six.string_types):
        os.remove(f)
    else:
        name = f.name
        if not f.closed:
            f.close()
        os.remove(name)


@contextmanager
def tmpfile_ctx():
    """
    Open an empty binary temporary file for writing.

    >>> if True:
    ...     import os
    ...     with tmpfile_ctx() as tmp:
    ...         fn = tmp.name
    ...         print(os.path.exists(fn))
    ...     print(os.path.exists(fn))
    True
    False
    """

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
        pass
    test_gc_before()
    test_gc_after()
    test_gc()

    import doctest
    doctest.testmod()
