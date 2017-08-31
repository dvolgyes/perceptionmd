#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

from kivy.core.window import Window
from kivy.uix.scatter import ScatterPlane
from kivy.clock import Clock


# Based on the idea:
# https://github.com/kivy/kivy/wiki/Viewport-with-fixed-resolution-autofit-to-window

class Viewport(ScatterPlane):

    def __init__(self, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('do_scale', False)
        kwargs.setdefault('do_translation', False)
        kwargs.setdefault('do_rotation', False)
        super(Viewport, self).__init__(**kwargs)
        Window.bind(system_size=self.on_window_resize)
        Clock.schedule_once(self.fit_to_window, -1)
        Clock.schedule_once(self.fit_to_window, 0.1)

    def on_window_resize(self, *args, **kwargs):
        self.fit_to_window()  # pragma: no cover

    def fit_to_window(self, *args):
        ratio = min(Window.width / float(self.width),
                    Window.height / float(self.height))
        self.scale = ratio

        self.center = Window.center
        for c in self.children:
            c.size = self.size

    def add_widget(self, w, *args, **kwargs):
        super(Viewport, self).add_widget(w, *args, **kwargs)
        w.size = self.size
