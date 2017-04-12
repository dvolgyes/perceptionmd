#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import


class Logger(object):
    """
    Basic logger class.

    >>> if True:
    ...    import tempfile
    ...    idx, f = tempfile.mkstemp()
    ...    logger=Logger(f)
    ...    logger.append("line")
    ...    logger.append_list(["line1","line2"])
    ...    logger("line3")
    ...    logger(["line4","line5"])
    ...    print(repr(logger).strip())
    line
    line1
    line2
    line3
    line4
    line5
    """

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

    def __repr__(self):
        result = ""
        with open(self.filename, "r") as f:
            for line in f.readlines():
                result += line
        return result

if __name__ == "__main__":
    import doctest
    doctest.testmod()
