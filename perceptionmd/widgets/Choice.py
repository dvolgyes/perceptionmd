#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import
import time
import random
from perceptionmd.widgets import ComboButtons
from kivy.properties import StringProperty, NumericProperty, DictProperty
from . import TaskScreen


class Choice(TaskScreen.TaskScreen):

    choice = NumericProperty(None)
    type = StringProperty(None)
    conditions = DictProperty()
    text = StringProperty()

    def __init__(self, *args, **kwargs):
        super(Choice, self).__init__(*args, **kwargs)

    def on_pre_leave(self, *args, **kwargs):
        leave_time = time.time()
        if self.type == 'INFO':
            self.log('- INFO: "%s", @time: %.3f' %
                     (self.name, (leave_time - self.start_time)))
        elif self.type == 'CHOICE':
            self.log('- CHOICE: "%s", @time: %.3f' % (self.name, (leave_time - self.start_time)))
            self.log('    options    = "%s"' % ('", "'.join(self.buttons.labels)))
            self.log('    {:<10} = {}' .format("selection", self.choice))
            self.log('    {:<10} = "{}"' .format(
                "label", self.text))
        else:
            assert(False)  # pragma: no cover
        self.log("")

    def move_on(self, *args, **kwargs):
        self.on_button(random.randrange(len(self.buttons.labels)))

    def on_button(self, button):
        self.buttons.selected = button
        self.choice = button
        self.text = self.buttons.labels[self.choice]
        if self.text in self.conditions:
            self.manager.current = self.conditions[self.text]
        else:
            self.manager.current = self.manager.next()

    def add_conditionals(self, lst):
        for item in lst:
            self.conditions[item.condition] = item.consequence

    def add_options(self, button_labels):
        self.buttons = ComboButtons.ComboButtons()
        self.buttons.labels = button_labels
        self.buttons.button_size = self.var['button_size']
        self.buttons.font_size = self.var['button_font_size']
        self.buttons.set_callback(self.on_button)
        self.layout.add_widget(self.buttons)
