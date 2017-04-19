#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import
import time
import threading
import re
import os
import math
import random
import numpy as np
from collections import defaultdict
import copy

from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.texture import Texture

from . import TaskScreen
from perceptionmd.utils import gc_after
from perceptionmd.volumes import RAW, DCM, colors
import perceptionmd.utils as utils

from kivy.properties import ObjectProperty, DictProperty, NumericProperty, ListProperty, BooleanProperty


class Pairwise(TaskScreen.TaskScreen):

    alpha = NumericProperty(1.0)
    colormap = ObjectProperty(None)
    base_colormap = ObjectProperty(None)
    wwidth = NumericProperty(-1)
    wcenter = NumericProperty(0)
    base_wwidth = NumericProperty(-1)
    base_wcenter = NumericProperty(0)
    z_pos = NumericProperty(0)
    z_max = NumericProperty(-1)
    volumedirs = ListProperty()
    serieses = ListProperty()
    loglines = ListProperty()
    texts = ListProperty()
    sources = ListProperty()
    base_layer_dirs = ListProperty()
    base_layer_serieses = ListProperty()
    choice_label = DictProperty()
    choice_idx = DictProperty()
    base = BooleanProperty(False)
    initialized_cmap = BooleanProperty(False)
    reference = BooleanProperty(False)

    rotate = NumericProperty(0)
    base_rotate = NumericProperty(0)
    plane = NumericProperty(0)
    base_plane = NumericProperty(0)
    flips = ListProperty()
    base_flips = ListProperty()

    def __init__(self, *args, **kwargs):
        super(Pairwise, self).__init__(**kwargs)
        self.total_time = 0
        self.wall_time = 0
        self.current_task_idx = -1
        self.lock = threading.Lock()
        self.black = None
        self.keypresses = defaultdict(lambda: False)
        self.min_refresh = 0.4
        self.winner = defaultdict(int)
        self.next_refresh = time.time()
        self.preselected_zpos = defaultdict(int)
        self.reference = kwargs.get('reference', False)

    def set_colormap(self, cmap, base_layer=False):
        if cmap is None:
            return
        if base_layer:
            self.base_colormap = colors.create_colormap(self.name + "_colormap", cmap)
        else:
            self.colormap = colors.create_colormap(self.name + "_colormap", cmap)

    def on_colormap(self, *args, **kwargs):
        self.initialized_cmap = False
        self.dcmview1.colormap = self.colormap
        self.dcmview2.colormap = self.colormap
        self.initialized_cmap = True

    def on_base_colormap(self, *args, **kwargs):
        self.dcmview1.base_colormap = self.base_colormap
        self.dcmview2.base_colormap = self.base_colormap

    def on_alpha(self, *args):
        self.alpha = np.clip(self.alpha, 0.0, 1.0).item()
        if self.base:
            self.alpha_text.text = "Alpha:"
            self.alpha_value.text = "%.2f" % self.alpha
            self.status_bar.size = (800, self.status_bar.size[1])
        else:
            self.status_bar.size = (600, self.status_bar.size[1])
            self.alpha_text.text = ""
            self.alpha_value.text = ""
        self.dcmview1.alpha = self.alpha
        self.dcmview2.alpha = self.alpha

    def on_wcenter(self, *args, **kwargs):
        self.wcenter = int(self.wcenter)
        self.dcmview1.wcenter = self.wcenter
        self.dcmview2.wcenter = self.wcenter
        if self.base:
            self.display_window_center.text = "%s (%s)" % (self.wcenter, self.base_wcenter)
        else:
            self.display_window_center.text = str(self.wcenter)

    def on_wwidth(self, *args, **kwargs):
        self.wwidth = int(self.wwidth)
        self.dcmview1.wwidth = self.wwidth
        self.dcmview2.wwidth = self.wwidth
        if self.base:
            self.display_window_width.text = "%s (%s)" % (self.wwidth, self.base_wwidth)
        else:
            self.display_window_width.text = str(self.wwidth)

    def on_base_wcenter(self, *args, **kwargs):
        self.base_wcenter = int(self.base_wcenter)
        self.dcmview1.base_wcenter = self.base_wcenter
        self.dcmview2.base_wcenter = self.base_wcenter
        if self.base:
            self.display_window_center.text = "%s (%s)" % (self.wcenter, self.base_wcenter)
        else:
            self.display_window_center.text = str(self.wcenter)

    def on_base_wwidth(self, *args, **kwargs):
        self.base_wwidth = int(self.base_wwidth)
        self.dcmview1.base_wwidth = self.base_wwidth
        self.dcmview2.base_wwidth = self.base_wwidth
        if self.base:
            self.display_window_width.text = "%s (%s)" % (self.wwidth, self.base_wwidth)
        else:
            self.display_window_width.text = str(self.wwidth)

    def on_z_max(self, *args, **kwargs):
        self.z_pos = int(min(self.z_pos, self.z_max))

    def on_z_pos(self, *args, **kwargs):
        self.z_pos = max(0, int(self.z_pos))
        self.axial_pos.text = " %s / %s " % (self.z_pos, self.z_max)
        self.dcmview1.z_pos = self.z_pos
        self.dcmview2.z_pos = self.z_pos

    def on_rotate(self, *args, **kwargs):
        self.rotate = int(self.rotate) % 4
        self.dcmview1.rotate = self.rotate
        self.dcmview2.rotate = self.rotate

    def on_flips(self, *args, **kwargs):
        self.dcmview1.flips = self.flips
        self.dcmview2.flips = self.flips

    def on_plane(self, *args, **kwargs):
        self.dcmview1.axis = self.plane
        self.dcmview2.axis = self.plane

    def on_base_rotate(self, *args, **kwargs):
        self.rotate = int(self.rotate) % 4
        self.dcmview1.base_rotate = self.base_rotate
        self.dcmview2.base_rotate = self.base_rotate

    def on_base_flips(self, *args, **kwargs):
        self.dcmview1.base_flips = self.base_flips
        self.dcmview2.base_flips = self.base_flips

    def on_base_plane(self, *args, **kwargs):
        self.dcmview1.base_axis = self.base_plane
        self.dcmview2.base_axis = self.base_plane

    def add_dirs(self, dirs, cache, base_layer=False):
        if dirs is not None:
            for s, d in enumerate(dirs):
                result = re.match(
                    r"(?P<protocol>[a-zA-Z]+)(\((?P<shape>\W.*)\))?::(?P<dirname>.*)", d[1:-1])
                if result:
                    protocol = result.group('protocol')
                    shape = result.group('shape')
                    if shape is None or len(shape) == 0:
                        shape = 'auto'
                    else:
                        shape = tuple(map(int, shape.split(",")))
                    dirname = result.group('dirname')
                else:
                    protocol = "DCM"
                    dirname = d[1:-1]
                    shape = 'auto'

                if protocol == "RAW":
                    dic = dict()
                    rawdir = RAW.RAWDIR(
                        dirname, dtype=np.dtype(self.var['raw_type']))
                    for idx, fn in enumerate(rawdir.volume_iterator()):
                        directory, filename = os.path.split(fn)
                        dic[idx] = (fn, directory)
                        if not base_layer:
                            self.loglines.append('        volume %s: "%s" ("%s")' % (idx, directory, filename))
                    if base_layer:
                        self.base_layer_serieses.append(dic)
                        self.base_layer_dirs.append(rawdir)
                    else:
                        self.serieses.append(dic)
                        self.volumedirs.append(rawdir)

                if protocol == "DCM":
                    dic = dict()
                    dicomdir = DCM.DICOMDIR(cache=cache)
                    self.loglines.append("    dicom-set %s:" % s)
                    for idx, series in enumerate(dicomdir.volume_iterator(dirname)):
                        directory = series
                        desc = dicomdir.UID2dir(series)
                        dic[idx] = (series, directory)
                        if not base_layer:
                            self.loglines.append('        volume %s: "%s" ("%s")' % (idx, directory, desc))
                    if base_layer:
                        self.base_layer_serieses.append(dic)
                        self.base_layer_dirs.append(dicomdir)
                    else:
                        self.serieses.append(dic)
                        self.volumedirs.append(dicomdir)

    def add_questions(self, questions):
        for question in questions:
            self.sources.append(question)
            src = question[1:-1]
            if src in self.contents:
                text = self.contents[src]
            else:
                if os.path.exists(src):
                    with open(src, "rt") as f:
                        text = f.read()
                else:
                    text = "File not found: '%s' " % src
            self.texts.append(text)

    def generate(self):
        result = []
        self.base = self.var['base_layer'] is not None
        for qidx, question in enumerate(self.texts):
            taskl = []
            for vidx, series in enumerate(self.serieses):
                if self.reference:
                    it = sorted(list(series.keys()))
                    if len(it) == 0:
                        continue
                    head, tail = it[0], it[1:]
                    for item in tail:
                        pair = [head, item]  # left is the default
                        if self.var['reference'] == 'right':
                            pair = [item, head]
                        elif self.var['reference'] == 'random':
                            random.shuffle(pair)

                        task = (qidx, vidx, pair)
                        taskl.append(task)
                else:
                    for pair in utils.random_combinations(series):
                        pair = list(pair)
                        random.shuffle(pair)
                        task = (qidx, vidx, pair)
                        taskl.append(task)
            random.shuffle(taskl)
            result.extend(taskl)
        self.tasklist = result
        self.loglines.append("    results:")
        self.loglines.append(
            "        question, set, left, right, answer button,   answer text  , selected volume,  @time, axial pos, wwidth, wcenter")

        self.plane = {'XY': 0, 'XZ': 1, 'YZ': 2}[self.var['plane']]
        self.flips = list(map(bool, self.var['flipped_axes']))
        self.rotate = int(self.var['rotate'])
        self.base_plane = {'XY': 0, 'XZ': 1, 'YZ': 2, None: self.plane}[self.var['plane']]
        self.alpha = self.var['alpha']
        self.property('alpha').dispatch(self)

        if self.var['base_flipped_axes'] is not None:
            self.base_flips = list(map(bool, self.var['base_flipped_axes']))
        else:
            self.base_flips = copy.copy(self.flips)
        if self.var['base_rotate'] is not None:
            self.base_rotate = int(self.var['base_rotate'])
        else:
            self.base_rotate = self.rotate

        self.next()
        self.update_scene()
        return result

    def next(self):
        if self.current_task_idx + 1 >= len(self.tasklist):
            return False
        self.current_task_idx += 1
        return True

    def update_scene(self, *args, **kwargs):
        self.disable_buttons()
        self.document.text = "Please wait for the next volumes..."
        self.axial_pos.text = " N/A "
        self.dcmview1.set_dummy_volume()
        self.dcmview2.set_dummy_volume()
        self.display_image(False)
        self.canvas.ask_update()
        self.update_thread = threading.Thread(target=self.up)
        self.update_thread.start()

    def up(self):
        time.sleep(self.min_refresh)
        with self.lock:
            task = self.tasklist[self.current_task_idx]
            (question, selected_set, (volID1, volID2)) = task
            series1 = self.serieses[selected_set][volID1][0]
            series2 = self.serieses[selected_set][volID2][0]

            self.dcmview1.set_volume(self.volumedirs[selected_set].volume(series1))
            self.dcmview2.set_volume(self.volumedirs[selected_set].volume(series2))

            if len(self.base_layer_dirs) > 0:
                base = self.base_layer_serieses[selected_set][0][0]
                self.dcmview1.set_volume(self.base_layer_dirs[selected_set].volume(base), True)
                self.dcmview2.set_volume(self.base_layer_dirs[selected_set].volume(base), True)

            self.z_max = min(self.dcmview1.z_max, self.dcmview2.z_max)
            poslist = self.var['z_position']
            display_window_center_list = self.var['display_window_center']
            display_window_width_list = self.var['display_window_width']
            base_display_window_center_list = self.var['base_display_window_center']
            base_display_window_width_list = self.var['base_display_window_width']
            self.set_colormap(self.var['colormap'])
            self.set_colormap(self.var['base_colormap'], True)

            if selected_set in self.preselected_zpos:
                self.z_pos = self.preselected_zpos[selected_set]
            else:
                self.z_pos = int(poslist[selected_set] if selected_set < len(poslist) else self.z_max // 2)

            if type(display_window_center_list) in (float, int):
                display_window_center_list = [display_window_center_list, ]
            if type(display_window_width_list) in (float, int):
                display_window_width_list = [display_window_width_list, ]

            if selected_set < len(display_window_center_list):
                self.wcenter = int(display_window_center_list[selected_set])
            if selected_set < len(display_window_width_list):
                self.wwidth = int(display_window_width_list[selected_set])

            if type(base_display_window_center_list) in (float, int):
                base_display_window_center_list = [base_display_window_center_list, ]
            if type(base_display_window_width_list) in (float, int):
                base_display_window_width_list = [base_display_window_width_list, ]

            if selected_set < len(base_display_window_center_list):
                self.base_wcenter = int(base_display_window_center_list[selected_set])
            else:
                self.base_wcenter = self.wcenter
            if selected_set < len(base_display_window_width_list):
                self.base_wwidth = int(base_display_window_width_list[selected_set])
            else:
                self.base_wwidth = self.wwidth
            self.alpha = self.var['alpha']

            self.dcmview1.orient_volume()
            self.dcmview2.orient_volume()

            self.property('z_pos').dispatch(self)

            if len(self.tasklist) > 1 + self.current_task_idx:
                nexttask = self.tasklist[self.current_task_idx + 1]
                (next_question, next_selected_set,
                 (next_volID1, next_volID2)) = nexttask
                next_series1 = self.serieses[next_selected_set][next_volID1][0]
                next_series2 = self.serieses[next_selected_set][next_volID2][0]
                self.volumedirs[next_selected_set].preload_volume(next_series1)
                self.volumedirs[next_selected_set].preload_volume(next_series2)

            self.document.text = self.texts[question]
            self.enable_buttons()
            self.initialized_cmap = True
            Clock.schedule_once(self.display_image, 0)
            Clock.schedule_once(self.display_image, self.min_refresh * 3)
            self.start_time = time.time()

    def disable_buttons(self):
        for button in self.choice_idx:
            button.disabled = True
            button.canvas.ask_update()

    def enable_buttons(self):
        for button in self.choice_idx:
            button.disabled = False
            button.canvas.ask_update()

    def on_initialized_cmap(self, *args, **kwargs):
        self.color_legend.texture = Texture.create(size=(self.color_legend.size))
        x = np.linspace(1, 1, self.color_legend.size[0])
        y = np.linspace(0, 255, self.color_legend.size[1])
        xv, yv = np.meshgrid(x, y)
        self.color_legend_gradient = yv.astype(np.uint8)
        if self.colormap is None:
            self.color_legend.texture.blit_buffer(
                self.color_legend_gradient.tostring(),
                colorfmt='luminance', bufferfmt='ubyte')
        else:
            cmap_str = (self.colormap(self.color_legend_gradient) * 255).astype(np.uint8).tostring()
            self.color_legend.texture.blit_buffer(cmap_str, colorfmt='rgba', bufferfmt='ubyte')

    def display_image(self, show=True):
        self.dcmview1.display_image(show)
        self.dcmview2.display_image(show)
        self.initialized_cmap = show

    def on_enter(self, *args, **kwargs):
        super(Pairwise, self).on_enter(**kwargs)
        self.generate()
        self.wall_time = time.time()
        self.start_time = time.time()
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self._keyboard.bind(on_key_up=self._on_keyboard_up)

    def on_pre_leave(self, *args, **kwargs):
        try:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        except:
            pass
        try:
            self._keyboard.unbind(on_key_up=self._on_keyboard_up)
        except:
            pass

        leave_time = time.time()
        if self.reference:
            self.log('- REFERENCE: "%s", @time: %.3f @effective_time: %.3f ' %
                     (self.name, leave_time - self.wall_time, self.total_time))
        else:
            self.log('- PAIR: "%s", @time: %.3f @effective_time: %.3f ' %
                     (self.name, leave_time - self.wall_time, self.total_time))

        self.log(self.loglines)
        self.loglines = []

        sorted_winner = sorted(self.winner.items(), key=lambda x: x[0], reverse=True)
        self.log("    winners:")
        for idx, wins in sorted_winner:
            if wins > 1:
                self.log("      {:>3} ({} wins)".format(idx, wins))
            else:
                self.log("      {:>3} ({}  win)".format(idx, wins))
        self.log("")

    def on_button(self, button, *args, **kwargs):
        now = time.time()
        i = self.choice_idx[button]
        task = self.tasklist[self.current_task_idx]
        (_, selected_set, (_, _)) = task

        elapsed = (now - self.start_time)
        self.total_time += elapsed
        selection = task[2][i]
        self.loglines.append(
            '        {:^8},{:^4},{:^5},{:^6},{:^14},{:^16},{:^16}, {:6.3f}, {:9}, {:^7}, {:^6}'.format(
                task[0],
                task[1],
                task[2][0],
                task[2][1],
                i,
                self.choice_label[i],
                selection,
                elapsed,
                self.z_pos,
                self.wwidth,
                self.wcenter))
        self.winner[selection] = self.winner[selection] + 1
        self.preselected_zpos[selected_set] = self.z_pos
        if not self.next():
            self.manager.current = self.manager.next()
        else:
            self.update_scene()

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        self.keypresses[keycode[1]] = True

        if keycode[1] == 'escape':
            keyboard.release()

        if keycode[1] == 'f3':
            self.plane = 0
            self.base_plane = 0

        if keycode[1] == 'f4':
            self.plane = 1
            self.base_plane = 1

        if keycode[1] == 'f5':
            self.plane = 2
            self.base_plane = 2

        if keycode[1] == 'f6':
            self.flips[0] ^= True
            self.base_flips[0] ^= True

        if keycode[1] == 'f7':
            self.flips[1] ^= True
            self.base_flips[1] ^= True

        if keycode[1] == 'f8':
            self.flips[2] ^= True
            self.base_flips[2] ^= True

        if keycode[1] == 'f9':
            self.rotate = (self.rotate + 1) % 4
            self.base_rotate = (self.base_rotate + 1) % 4

        if keycode[1] == 'f10':
            self.rotate = (self.rotate + 3) % 4
            self.base_rotate = (self.base_rotate + 3) % 4

        if keycode[1] in ['f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10']:
            self.dcmview1.orient_volume()
            self.dcmview2.orient_volume()
            self.dcmview1.display_image()
            self.dcmview2.display_image()
            return True

        return True

    def _on_keyboard_up(self, keyboard, keycode):
        self.keypresses[keycode[1]] = False
        return True

    def add_options(self, button_labels):
        self.buttons = dict()
        self.dcmview1.mainw = self
        self.dcmview2.mainw = self

        for idx, label in enumerate(button_labels):
            btn = Button(text=label)
            self.choice_idx[btn] = idx
            self.choice_label[idx] = label

            btn.size_hint = self.layout.size_hint
            btn.size = self.layout.size
            btn.height = self.var['button_size']
            btn.font_size = self.var['button_font_size']

            self.buttons[btn] = (idx, btn.text)
            btn.bind(on_press=lambda x: self.on_button(x))
            self.layout.add_widget(btn)

    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return
        if 'button' in touch.profile:
            if self.keypresses['shift']:
                if touch.button == 'scrolldown':
                    self.alpha += 0.05
                if touch.button == 'scrollup':
                    self.alpha -= 0.05
            else:
                if touch.button == 'scrolldown':
                    self.on_scroll(1)
                if touch.button == 'scrollup':
                    self.on_scroll(-1)
            if touch.button == 'left':
                for b in self.buttons:
                    if b.on_touch_down(touch):
                        return True

            if touch.button in (self.var['display_window_mouse_button'], self.var['display_window_mouse_button2'],
                                self.var['mouse_window_scroll_button']):
                touch.grab(self)
                self.tzpos = self.z_pos
                self.touch_pos = touch.pos
                self.tcenter = self.wcenter
                self.twidth = self.wwidth
                return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if touch.button in (self.var['display_window_mouse_button'], self.var['display_window_mouse_button2']):
                dx, dy = touch.dpos
#                r = np.sqrt(dx * dx + dy * dy)
                direction = abs(dx) > abs(dy)
                angle = int(math.atan2(dy, dx) / math.pi * 4) + 4
                speed = 4 if self.keypresses['ctrl'] or self.keypresses['rctrl'] else 1
                base = self.keypresses['shift'] or self.keypresses['rshift']

                if base:
                    if (angle % 2 == 0):
                        if direction == (int(self.var['display_window_center_vertical_mouse']) == 0):
                            delta = int(dx * speed)
                            self.base_wwidth = max(10, self.base_wwidth + delta)
                        else:
                            delta = int(dy * speed)
                            self.base_wcenter = self.base_wcenter + delta
                else:
                    if (angle % 2 == 0):
                        if direction == (int(self.var['display_window_center_vertical_mouse']) == 0):
                            delta = int(dx * speed)
                            self.wwidth = max(10, self.wwidth + delta)
                        else:
                            delta = int(dy * speed)
                            self.wcenter = self.wcenter + delta

                self.display_image()
            elif touch.button == self.var['mouse_window_scroll_button']:
                dx, dy = touch.dpos
#                r = np.sqrt(dx * dx + dy * dy)
                direction = abs(dx) > abs(dy)
                angle = int(math.atan2(dy, dx) / math.pi * 4) + 4
                if (angle % 2 == 0):
                    dz = (touch.pos[1] - self.touch_pos[1])
                    self.z_pos = self.tzpos + dz * 1.0
                    self.display_image()
            else:
                pass

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
        else:
            pass

    def on_scroll(self, direction):
        with self.lock:
            speed = 1
            if self.keypresses['ctrl'] or self.keypresses['rctrl']:
                speed = 5
#            if False:
#                pass
#            #~ elif self.keypresses['shift']:
#                #~ self.wcenter += direction*speed*2
#                #~ self.display_window_center.text = str(self.wcenter)
#                #~ self.dcmview1.set_window(self.wcenter,self.wwidth)
#                #~ self.dcmview2.set_window(self.wcenter,self.wwidth)
#            #~ elif self.keypresses['ctrl'] or self.keypresses['rctrl']:
#                #~ self.wwidth += direction*speed*4
#                #~ self.wwidth = max(2,self.wwidth)
#                #~ self.display_window_width.text = str(self.wwidth)
#                #~ self.dcmview1.set_window(self.wcenter,self.wwidth)
#                #~ self.dcmview2.set_window(self.wcenter,self.wwidth)
            self.z_pos = max(0, int(self.z_pos + direction * speed))
            self.display_image()
            return True

    @gc_after
    def clear(self):
        self.dcmview1.clear()
        self.dcmview2.clear()
        for dirs in self.volumedirs:
            dirs.clear()
        del self.volumedirs[:]
