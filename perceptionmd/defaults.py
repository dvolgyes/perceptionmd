#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals
from collections import defaultdict
import time


default_settings = defaultdict()


default_settings.update({
    'font_size': 32,
    'logfile': 'results.txt',
    'random_seed': time.time(),
    'input_label_font_size': 32,
    'input_field_font_size': 32,
    'title_font_size': 64,
    'background_color': 'None',
    'button_font_size': 32,
    'button_size': 32,
    'button_font_color': 'None',
    'button_background_color': 'None',
    'fullscreen': 0,
    'window_height': 1080,
    'window_width': 1920,
    'screenshot_hotkey': 'shift+f12',
    'fullscreen_hotkey': 'f11',
    'display_window_mouse_button': 'middle',
    'display_window_mouse_button2': 'left',
    'display_window_center_vertical_mouse': 0,
    'mouse_window_scroll_button': 'right',
    'reset_settings_between_questions': False,
    'reset_settings_immediately': False,
    'flipped_axes': (0, 1, 0),
    'plane': 'XY',
    'rotate': 0,
    'base_flipped_axes': None,
    'base_plane': None,
    'base_rotate': None,
    'z_position': [],
    'display_window_center': [0, ],
    'display_window_width': [400, ],
    'colormap': None,
    'raw_type': 'float32',
    'reference': 'left',
    'base_layer': None,
    'base_colormap': None,
    'alpha': 1.0,
    'text_input_ratio': 2.0,
    'screenshot_directory': '.'
})
