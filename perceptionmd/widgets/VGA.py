#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import
from . import TaskScreen
import time


class VGA(TaskScreen.TaskScreen):

    def __init__(self, *args, **kwargs):
        super(VGA, self).__init__(*args, **kwargs)
        self.start_time = None

    def on_pre_leave(self, *args, **kwargs):
        leave_time = time.time()
        self.log('- VGA: "%s", @time: %.3f' %
                 (self.name, (leave_time - self.start_time)))
        self.log("")

    def on_button_press(self, *args, **kwargs):
        self.manager.current = self.manager.next()

    def set(self, *args, **kwargs):
        pass
