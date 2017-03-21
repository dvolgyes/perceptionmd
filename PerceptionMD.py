#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import perceptionmd
import sys
perceptionmd.run(*[unicode(x,'utf-8') for x in sys.argv])
