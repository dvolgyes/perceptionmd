#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import
import perceptionmd
import sys

perceptionmd.run(*[u"%s" % x for x in sys.argv])
