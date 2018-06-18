#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import perceptionmd
import sys
import six

if six.PY2:
    perceptionmd.run(*[u'{}'.format(x) for x in sys.argv])
else:
    perceptionmd.run(*sys.argv)
