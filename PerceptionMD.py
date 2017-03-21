#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import perceptionmd
import sys
import six

if six.PY2:
    perceptionmd.run(*[unicode(x,'utf-8') for x in sys.argv])
else:
    perceptionmd.run(*sys.argv)
