#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import
from . import TaskScreen
import time
import random
from kivy.uix.button import Button

class Choice(TaskScreen.TaskScreen):

    def __init__(self, *args, **kwargs):
        super(Choice, self).__init__(*args, **kwargs)
        self.type = None
        self.conditions = dict()
        self.choice_label = dict()
        self.names_to_screen = dict()
        self.start_time = None

    def on_pre_leave(self, *args, **kwargs):
        leave_time = time.time()
        if self.type == 'INFO':
            self.log('- INFO: "%s", @time: %.3f' %
                     (self.name, (leave_time - self.start_time)))
        elif self.type == 'CHOICE':
            self.log('- CHOICE: "%s", @time: %.3f' %
                     (self.name, (leave_time - self.start_time)))
            self.log('    {:<10} = {}' .format("selection", self.choice))
            self.log('    {:<10} = {}' .format(
                "label", self.choice_label[self.choice]))
        else:
            assert(False)
        self.log("")

    def move_on(self, *args, **kwargs):
        self.on_button(random.choice(list(self.buttons.keys())))

    def on_button(self, button):
        self.choice, key = self.buttons[button]
        if key in self.conditions:
            self.manager.current = self.conditions[key]
        else:
            self.manager.current = self.manager.next()

    def add_conditionals(self, lst):
        for item in lst:
            self.conditions[item.condition] = item.consequence

    def set(self, *args, **kwargs):
        pass

    def add_options(self, button_labels):
        self.buttons = dict()
        for idx, label in enumerate(button_labels):
            self.choice_label[idx] = label
            btn = Button(text=label)
            btn.size_hint = self.layout.size_hint
            btn.size = self.layout.size
            btn.height = self.var['button_size']
            btn.font_size = self.var['button_font_size']

            self.buttons[btn] = (idx, btn.text)
            btn.bind(on_press=lambda x: self.on_button(x))
            self.layout.add_widget(btn)
