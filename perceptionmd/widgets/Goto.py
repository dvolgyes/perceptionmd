#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

from . import TaskScreen

class Goto(TaskScreen.TaskScreen):

    def __init__(self, *args, **kwargs):
        super(Goto, self).__init__(*args, **kwargs)

    def on_pre_enter(self):
        self.manager.current = self.label


