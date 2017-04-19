#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import time
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from perceptionmd.utils import gc_after
from abc import abstractmethod
from kivy.properties import BooleanProperty


class TaskScreen(Screen):

    def __init__(self, *args, **kwargs):
        super(TaskScreen, self).__init__(*args, **kwargs)
        self.start_time = time.time()
        self.automated_test = kwargs.get('automated_test', False)
        self.name = kwargs['name']

    @abstractmethod
    def on_button_press(self, *args, **kwargs):  # pragma: no cover
        pass

    def move_on(self, *args, **kwargs):
        if self.manager.current == self.name:
            self.manager.current = self.manager.next()

    def on_enter(self, *args, **kwargs):
        self.start_time = time.time()
        if self.automated_test:
            print('screen has been loaded: %s' % self.name)
        if self.automated_test:
            Clock.schedule_once(self.move_on, 5)
            Clock.schedule_once(self.move_on, 95)

    @abstractmethod
    def on_key_down(self, win, key, scancode, string, modifiers):  # pragma: no cover
        pass

    def clear(self, *args, **kwargs):  # pragma: no cover
        pass

    @gc_after
    def on_leave(self, *args, **kwargs):
        self.clear()
