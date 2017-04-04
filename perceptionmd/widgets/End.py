#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

from . import TaskScreen
from kivy.app import App


class End(TaskScreen.TaskScreen):

    def __init__(self, *args, **kwargs):
        super(End, self).__init__(*args, **kwargs)

    def on_pre_enter(self):
        App.get_running_app().stop()
