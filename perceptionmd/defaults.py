#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
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
'button_font_size': 48,
'button_size': 48,
'button_font_color': 'None',
'button_background_color': 'None',
'full_screen': 1,
'window_height': 1080,
'window_width': 1920,
'screenshot_hotkey': 'shift+f12',
'fullscreen_hotkey': 'f11',
'HU_mouse_button': 'middle',
'HU_mouse_button2': 'left',
'mouse_window_scroll_button': 'right',
'flipped_axes': (0,0,0),
'plane': 'XY',
'rotate': 0,
'z_position': [],
'hu_center': [],
'hu_width': [],
'colormap': None,
'raw_type': 'float32'
})