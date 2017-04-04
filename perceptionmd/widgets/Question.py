#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import
from . import TaskScreen
import time
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput


class Question(TaskScreen.TaskScreen):

    def __init__(self, *args, **kwargs):
        super(Question, self).__init__(*args, **kwargs)
        self.questions = []
        self.variables = dict()
        self.start_time = None
        self.focuses = []

    def add_questions(self, qs):
        for q in qs:
            label = Label(text=q.message)
            input = TextInput()
            label.font_size = self.var['input_label_font_size']
            input.font_size = self.var['input_field_font_size']
            self.variables[q.variable] = (input, q.type)
            self.layout.add_widget(label)
            self.layout.add_widget(input)
            self.focuses.append(input)
            input.is_focusable = True
            input.write_tab = False
        self.set_focuses()
        self.button.height = self.var['button_size']
        self.button.font_size = self.var['button_font_size']

    def set_focuses(self):
        if len(self.focuses) > 0:
            self.focuses[0].focus = True
            for i in range(len(self.focuses) - 1):
                self.focuses[i].focus_next = self.focuses[i + 1]
                self.focuses[i + 1].focus_previous = self.focuses[i]

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
