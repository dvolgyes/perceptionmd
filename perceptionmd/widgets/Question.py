#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import
import time
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.properties import ListProperty, DictProperty, NumericProperty
from . import TaskScreen


class Question(TaskScreen.TaskScreen):

    questions = ListProperty()
    variables = DictProperty()
    ratio = NumericProperty()

    def __init__(self, *args, **kwargs):
        super(Question, self).__init__(*args, **kwargs)
        self.ratio = 2

    def on_ratio(self, *args, **kwargs):
        self.layout.size_hint = (1, 1)
        self.document.size_hint = (self.layout.size_hint[0], self.ratio)

    def on_questions(self, *args, **kwargs):
        for q in self.questions:
            label = Label(text=q.message)
            input = TextInput()
            label.font_size = self.var['input_label_font_size']
            input.font_size = self.var['input_field_font_size']
            self.variables[q.variable] = (input, q.type)
            self.layout.add_widget(label)
            self.layout.add_widget(input)
            input.is_focusable = True
            input.write_tab = False
        self.button.height = self.var['button_size']
        self.button.font_size = self.var['button_font_size']

    def on_pre_leave(self, *args, **kwargs):
        leave_time = time.time()
        self.log('- QUESTION: "%s", @time: %.3f' %
                 (self.name, (leave_time - self.start_time)))
        for key in self.variables:
            value = self.variables[key][0].text
            field_type = self.variables[key][1]
            self.variables[key] = value
            if field_type == "STRING":
                self.log('    {:<10} = "{}"' .format(key, value))
            else:
                if len(value) == 0:
                    value = 0
                self.log('    {:<10} = {}' .format(key, value))

        self.log("")

    def on_button_press(self, *args, **kwargs):
        self.manager.current = self.manager.next()
