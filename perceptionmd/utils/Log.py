#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import


class Logger(object):

    def __init__(self, filename):
        self.filename = filename
        with open(self.filename, "a+"):
            pass

    def append(self, line):
        with open(self.filename, "a") as f:
            f.write(line.rstrip())
            f.write("\n")

    def append_list(self, lst):
        for line in lst:
            self.append(line)

    def __call__(self, argument):
        if isinstance(argument, list):
            self.append_list(argument)
        else:
            self.append(argument)
