#!/usr/bin/python
# -*- coding: utf-8 -*-

from kivy.uix.widget import Widget
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivy.uix.togglebutton import ToggleButton


class ComboButtons(Widget):

    labels = ListProperty()
    orientation = StringProperty()
    selected = NumericProperty(-1)
    font_size = NumericProperty(16)
    button_size = NumericProperty(16)
    text = StringProperty('')
    group = StringProperty()
    allow_no_selection = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        super(ComboButtons, self).__init__(*args, **kwargs)
        self.callback = self.noop

    def on_button_size(self, *args, **kwargs):
        self.layout.size = (self.layout.size[0], self.button_size)
        for child in self.layout.children:
            child.size = child.size[0], self.button_size
            child.size_hint = 1, None

    def on_font_size(self, *args, **kwargs):
        for child in self.layout.children:
            child.font_size = self.font_size

    def on_labels(self, *args, **kwargs):
        self.layout.clear_widgets()
        self.layout.size = self.layout.size[0], self.button_size
        for label in self.labels:
            widget = ToggleButton(
                text=label,
                group=self.group,
                allow_no_selection=self.allow_no_selection,
                state='normal',
            )

            widget.font_size = self.font_size
            self.layout.add_widget(widget)

        if self.text != '':
            self.selected = (self.labels).index(self.text)
        if self.selected >= 0:
            self.layout.children[len(self.layout.children) - 1 - self.selected].state = 'down'

    def noop(self, *args, **kwargs):  # pragma: no cover
        pass

    def set_callback(self, f):
        self.callback = f

    def on_selected(self, obj, value):
        if len(self.layout.children) > 0:
            for i in range(len(self.layout.children)):
                if i == value:
                    self.layout.children[len(self.layout.children) - 1 - i].state = 'down'
                else:
                    self.layout.children[len(self.layout.children) - 1 - i].state = 'normal'
            self.text = self.labels[value]
            self.callback(value)

    def on_text(self, obj, value):
        try:
            self.selected = (self.labels).index(value)
        except Exception:  # pragma: no cover
            pass

    def on_touch_down(self, touch):
        for i in range(len(self.layout.children)):
            child = self.layout.children[i]
            if child.on_touch_down(touch):
                self.selected = len(self.layout.children) - 1 - i
                return True
        return False
