#!/usr/bin/python2
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import sys
import os
import time
import datetime
import math
import numpy as np
import random
import cachetools
import operator
import threading
import re
import six
from collections import defaultdict

from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.properties import ObjectProperty, ListProperty
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.config import Config
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.uix.scatter import ScatterPlane
import textx
import textx.metamodel

import perceptionmd.volumes.DCM as DCM
from perceptionmd.volumes import RAW
import perceptionmd.volumes.colors as colors

from perceptionmd.defaults import default_settings
import perceptionmd.utils as utils
from perceptionmd.utils import gc_after


def KV(kvs, key):
    for kv in kvs:
        if kv.key == key:
            return kv.value
    return None


class Logger():

    def __init__(self, filename):
        self.filename = filename
        with open(self.filename, "a+"):
            pass

    def append(self, line):
        with open(self.filename, "a") as f:
            f.write(line.rstrip())
            f.write("\n")

    def append_list(self, lst):
        for line in lst:
            self.append(line)

    def __call__(self, argument):
        if isinstance(argument, list):
            self.append_list(argument)
        else:
            self.append(argument)


class TaskScreen(Screen):

    def __init__(self, *args, **kwargs):
        super(TaskScreen, self).__init__(*args, **kwargs)
        self.start_time = None

    def on_button_press(self, *args, **kwargs):
        self.manager.current = self.manager.next()

    def move_on(self, *args, **kwargs):
        self.manager.current = self.manager.next()

    def on_enter(self, *args, **kwargs):
        self.start_time = time.time()
        if self.automated_test:
            Clock.schedule_once(self.move_on, 3)

    def on_key_down(self, win, key, scancode, string, modifiers):
        pass

    def clear(self, *args, **kwargs):
        pass

    @gc_after
    def on_leave(self, *args, **kwargs):
        self.clear()


class Goto(TaskScreen):

    def __init__(self, *args, **kwargs):
        super(Goto, self).__init__(*args, **kwargs)

    def on_pre_enter(self):
        self.manager.current = self.label


class End(TaskScreen):

    def __init__(self, *args, **kwargs):
        super(End, self).__init__(*args, **kwargs)

    def on_pre_enter(self):
        App.get_running_app().stop()


class DICOMVIEW(BoxLayout):

    def __init__(self, *args, **kwargs):
        super(DICOMVIEW, self).__init__(**kwargs)
        self.mainw = None
        self.dcm_image = ObjectProperty(None)
        self.rel = ListProperty([0, 0])
        self.empty = np.zeros(shape=(512, 512), dtype=np.uint8)
        self.black = np.ones(shape=(1, 512, 512), dtype=np.float32) * -32000
        self.array = np.zeros(shape=(1, 512, 512), dtype=np.uint8)
        self.volume = np.zeros(shape=(1, 512, 512), dtype=np.uint8)
        self.z_pos = 0
        self.z_max = 0
        self.img_texture = Texture.create(size=(512, 512))
        self.wcenter = 0
        self.wwidth = 100
        self.initialized = False
        self.colormap = None
        self.flips = [False, False, False]
        self.rotate = 0
        self.axis = 0
        self.core_volume = self.volume

    @gc_after
    def clear(self):
        self.set_dummy_volume()

    def set_colormap(self, cmap):
        self.colormap = cmap
        self.set_window(self.wcenter, self.wwidth)

    def set_volume(self, volume):
        assert(volume is not None)
        self.core_volume = volume
        self.volume = volume
        self.orient_volume()

    def orient_volume(self):
        self.volume = self.core_volume
        if self.axis > 0:
            self.volume = np.swapaxes(self.volume, 0, self.axis)
        if self.rotate > 0:
            t = np.swapaxes(self.volume, 0, 2)
            t = np.rot90(t, k=self.rotate)
            self.volume = np.swapaxes(t, 0, 2)

        if self.flips[0]:
            self.volume = self.volume[::-1, ...]
        if self.flips[1]:
            self.volume = self.volume[:, ::-1, ...]
        if self.flips[2]:
            self.volume = self.volume[..., ::-1]

        self.z_max = self.volume.shape[0] - 1
        self.z_pos = int(min(self.z_pos, self.z_max))
        self.set_window(self.wcenter, self.wwidth)

    def set_dummy_volume(self):
        self.set_volume(self.black.reshape(1, 512, 512))

    def set_window(self, center, width):
        """
        :type center: int, >-1000, <3000
        :type width: int, >0
        """
        self.wcenter = center
        self.wwidth = width

    def set_z(self, z):
        """
        :type z: int, >=0
        """
        new_z = int(max(0, min(self.z_max, z)))
        self.z_pos = new_z

    def on_scroll(self, touch, rel):
        return None

    def blit(self, image, colorfmt, bufferfmt):
        if self.dcm_image.texture.size != image.shape[0:2]:
            self.dcm_image.texture = Texture.create(image.shape[0:2])
            self.empty = np.zeros(shape=self.dcm_image.texture.size[0:2], dtype=np.uint8)
        self.dcm_image.texture.blit_buffer(image.ravel(), colorfmt=colorfmt, bufferfmt=bufferfmt)

    def display_image(self, show=True):
        if not self.initialized:
            self.dcm_image.texture = self.img_texture
            self.initialized = True
            self.blit(self.empty, colorfmt='luminance', bufferfmt='ubyte')
        if show:
            while self.volume is None:
                self.log("ERROR: Volume is None!")
                print("ERROR: Volume is None!")
                return
            shift = self.wcenter - self.wwidth / 2.0
            array = np.clip((self.volume[self.z_pos, :, :] - shift) / (self.wwidth / 255.0), 0, 255).astype(np.uint8)
            if array.shape[0] != array.shape[1]:
                array = utils.padding_square(np.clip(array, 0, 255).astype(np.uint8))

            if self.colormap is not None:
                slice_str = (self.colormap(array) * 255).astype(np.uint8)
                self.blit(slice_str.reshape(array.shape + (-1,)), colorfmt='rgba', bufferfmt='ubyte')
            else:
                self.blit(array, 'luminance', 'ubyte')
        else:
            self.blit(self.empty, 'luminance', 'ubyte')

        self.dcm_image.canvas.ask_update()
        self.canvas.ask_update()


class Pair(TaskScreen):

    def __init__(self, *args, **kwargs):
        super(Pair, self).__init__(**kwargs)
        self.start_time = None
        self.total_time = 0
        self.wall_time = None
        self.volumedirs = []
        self.serieses = []
        self.loglines = []
        self.texts = []
        self.sources = []
        self.choice_label = dict()
        self.choice_idx = dict()
        self.current_task_idx = -1
        self.lock = threading.Lock()
        self.black = None
        self.z_pos = 0
        self.z_max = 0
        self.wwidth = 400
        self.wcenter = 20
        self.keypresses = defaultdict(lambda: False)
        self.min_refresh = 0.4
        self.winner = defaultdict(int)
        self.initialized_cmap = False
        self.colormap = None
        self.next_refresh = time.time()
        self.preselected_zpos = defaultdict(int)

    def set_colormap(self, cmap):
        if cmap is None:
            return
        self.colormap = colors.create_colormap(self.name + "_colormap", cmap)
        self.dcmview1.set_colormap(self.colormap)
        self.dcmview2.set_colormap(self.colormap)

    def add_dirs(self, dirs, cache):
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
                self.serieses.append(dict())
                rawdir = RAW.RAWDIR(
                    dirname, dtype=np.dtype(self.var['raw_type']))
                for idx, fn in enumerate(rawdir.volume_iterator()):
                    directory, filename = os.path.split(fn)
                    self.serieses[-1][idx] = (fn, directory)
                    self.loglines.append(
                        '        volume %s: "%s" ("%s")' % (idx, directory, filename))
                self.volumedirs.append(rawdir)

            if protocol == "DCM":
                self.serieses.append(dict())
                dicomdir = DCM.DICOMDIR(cache=cache)
                self.loglines.append("    dicom-set %s:" % s)
                for idx, series in enumerate(dicomdir.volume_iterator(dirname)):
                    directory = series
                    desc = dicomdir.UID2dir(series)
                    #~ directory = os.path.dirname(dicomdir._files[series][-1][1])
                    #~ desc = dicomdir._texts[series]
                    self.serieses[-1][idx] = (series, directory)
                    self.loglines.append(
                        '        volume %s: "%s" ("%s")' % (idx, directory, desc))
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
                    text = "File not found: %s " % src
            self.texts.append(text)

    def generate(self):
        result = []
        for qidx, question in enumerate(self.texts):
            taskl = []
            for vidx, series in enumerate(self.serieses):
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
            "        question, set, left, right, answer button, answer text, selected volume,  @time, axial pos, wwidth, wcenter")

        self.plane = {'XY': 0, 'XZ': 1, 'YZ': 2}[self.var['plane']]
        self.flips = list(map(bool, self.var['flipped_axes']))
        self.rotate = self.var['rotate']
        self.next()
        self.update_scene()
        return result

    def next(self):
        self.current_task_idx += 1
        if self.current_task_idx >= len(self.tasklist):
            return False
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
            self.dcmview1.rotate = self.rotate
            self.dcmview1.flips = self.flips
            self.dcmview1.axis = self.plane
            self.dcmview2.rotate = self.rotate
            self.dcmview2.flips = self.flips
            self.dcmview2.axis = self.plane

            self.dcmview1.set_volume(
                self.volumedirs[selected_set].volume(series1))
            self.dcmview2.set_volume(
                self.volumedirs[selected_set].volume(series2))

            self.z_max = min(self.dcmview1.z_max, self.dcmview2.z_max)
            poslist = self.var['z_position']
            hu_center_list = self.var['hu_center']
            hu_width_list = self.var['hu_width']
            self.set_colormap(self.var['colormap'])

            if selected_set in self.preselected_zpos:
                self.z_pos = self.preselected_zpos[selected_set]
            else:
                self.z_pos = int(poslist[selected_set] if selected_set < len(
                    poslist) else self.z_max // 2)

            if type(hu_center_list) in (float, int):
                hu_center_list = [hu_center_list, ]
            if type(hu_width_list) in (float, int):
                hu_width_list = [hu_width_list, ]

            if selected_set < len(hu_center_list):
                self.wcenter = int(hu_center_list[selected_set])
            if selected_set < len(hu_width_list):
                self.wwidth = int(hu_width_list[selected_set])

            self.dcmview1.set_window(self.wcenter, self.wwidth)
            self.dcmview2.set_window(self.wcenter, self.wwidth)
            self.dcmview1.orient_volume()
            self.dcmview2.orient_volume()

            if len(self.tasklist) > 1 + self.current_task_idx:
                nexttask = self.tasklist[self.current_task_idx + 1]
                (next_question, next_selected_set,
                 (next_volID1, next_volID2)) = nexttask
                next_series1 = self.serieses[next_selected_set][next_volID1][0]
                next_series2 = self.serieses[next_selected_set][next_volID2][0]
                self.volumedirs[next_selected_set].preload_volume(next_series1)
                self.volumedirs[next_selected_set].preload_volume(next_series2)

            self.axial_pos.text = " %s / %s " % (int(self.z_pos), int(self.z_max))
            self.hu_center.text = str(int(self.wcenter))
            self.hu_width.text = str(int(self.wwidth))
            self.dcmview1.set_z(self.z_pos)
            self.dcmview2.set_z(self.z_pos)
            self.document.text = self.texts[question]
            self.enable_buttons()
            Clock.schedule_once(self.display_image)
            Clock.schedule_once(self.display_image, self.min_refresh)
            self.start_time = time.time()

    def disable_buttons(self):
        for button in self.choice_idx:
            button.disabled = True
            button.canvas.ask_update()

    def enable_buttons(self):
        for button in self.choice_idx:
            button.disabled = False
            button.canvas.ask_update()

    def display_image(self, show=True):
        self.dcmview1.display_image(show)
        self.dcmview2.display_image(show)
        if show:
            if not self.initialized_cmap:
                self.color_legend.texture = Texture.create(
                    size=(self.color_legend.size))
                x = np.linspace(1, 1, self.color_legend.size[0])
                y = np.linspace(0, 255, self.color_legend.size[1])
                xv, yv = np.meshgrid(x, y)
                self.color_legend_gradient = yv.astype(np.uint8)
            if self.colormap is None:
                self.color_legend.texture.blit_buffer(
                    self.color_legend_gradient.tostring(), colorfmt='luminance', bufferfmt='ubyte')
            else:
                cmap_str = (self.colormap(self.color_legend_gradient) * 255).astype(np.uint8).tostring()
                self.color_legend.texture.blit_buffer(cmap_str, colorfmt='rgba', bufferfmt='ubyte')

    def on_enter(self, *args, **kwargs):
        self.set()
        self.wall_time = time.time()
        self.start_time = time.time()
        self._keyboard = Window.request_keyboard(
            self._keyboard_closed, self, 'text')
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self._keyboard.bind(on_key_up=self._on_keyboard_up)

    def on_pre_leave(self, *args, **kwargs):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard.unbind(on_key_up=self._on_keyboard_up)

        leave_time = time.time()
        self.log('- PAIR: "%s", @time: %.3f @effective_time: %.3f ' %
                 (self.name, leave_time - self.wall_time, self.total_time))
        self.log(self.loglines)
        self.loglines = []

        sorted_winner = sorted(self.winner.items(),
                               key=operator.itemgetter(1), reverse=True)
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
        #~ question,set,left,right,answerselectedvolume
        selection = task[2][i]
        self.loglines.append(
            '        {:^8},{:^4},{:^5},{:^6},{:^14},{:^12},{:^16}, {:6.3f}, {:9}, {:^7}, {:^6}'.format(
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
        #~ self.manager.current = self.manager.next()
        # save current selection
        if not self.next():
            self.manager.current = self.manager.next()
        else:
            self.update_scene()
        #~ else:
            #~ # set up new scene
            #~ pass

    def set(self, *args, **kwargs):
        self.generate()

    def _keyboard_closed(self):
        pass
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        self.keypresses[keycode[1]] = True

        if keycode[1] == 'escape':
            keyboard.release()

        if keycode[1] == 'f3':
            self.dcmview1.axis = 0
            self.dcmview2.axis = 0

        if keycode[1] == 'f4':
            self.dcmview1.axis = 1
            self.dcmview2.axis = 1

        if keycode[1] == 'f5':
            self.dcmview1.axis = 2
            self.dcmview2.axis = 2

        if keycode[1] == 'f6':
            self.dcmview1.flips[0] = not self.dcmview1.flips[0]
            self.dcmview2.flips[0] = self.dcmview1.flips[0]

        if keycode[1] == 'f7':
            self.dcmview1.flips[1] = not self.dcmview1.flips[1]
            self.dcmview2.flips[1] = self.dcmview1.flips[1]

        if keycode[1] == 'f8':
            self.dcmview1.flips[2] = not self.dcmview1.flips[2]
            self.dcmview2.flips[2] = self.dcmview1.flips[2]

        if keycode[1] == 'f9':
            self.dcmview1.rotate = (self.dcmview1.rotate + 1) % 4
            self.dcmview2.rotate = self.dcmview1.rotate

        if keycode[1] == 'f10':
            self.dcmview1.rotate = (self.dcmview1.rotate + 3) % 4
            self.dcmview2.rotate = self.dcmview1.rotate

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

    #~ on_touch_down:
        #~ root.on_scroll(args[1])
    #~ on_touch_move:
        #~ root.on_move(args)

    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return
        if 'button' in touch.profile:
            if touch.button == 'scrolldown':
                self.on_scroll(1)
            if touch.button == 'scrollup':
                self.on_scroll(-1)
            if touch.button == 'left':
                for b in self.buttons:
                    if b.on_touch_down(touch):
                        return True

            if touch.button in (self.var['HU_mouse_button'], self.var['HU_mouse_button2'],
                                self.var['mouse_window_scroll_button']):
                touch.grab(self)
                self.tzpos = self.z_pos
                self.touch_pos = touch.pos
                self.tcenter = self.wcenter
                self.twidth = self.wwidth
                return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if touch.button in (self.var['HU_mouse_button'], self.var['HU_mouse_button2']):
                dx, dy = touch.dpos
#                r = np.sqrt(dx * dx + dy * dy)
                direction = abs(dx) > abs(dy)
                angle = int(math.atan2(dy, dx) / math.pi * 4) + 4
                speed = 4 if self.keypresses['ctrl'] or self.keypresses['rctrl'] else 1

                if (angle % 2 == 0):
                    if direction == (int(self.var['HU_center_vertical_mouse']) == 0):
                        delta = int(dx) * speed
                        self.wwidth = max(10, self.wwidth + delta)
                    else:
                        delta = int(dy) * speed
                        self.wcenter = self.wcenter + delta
                self.set_window()
                self.display_image()
            elif touch.button == self.var['mouse_window_scroll_button']:
                dx, dy = touch.dpos
#                r = np.sqrt(dx * dx + dy * dy)
                direction = abs(dx) > abs(dy)
                angle = int(math.atan2(dy, dx) / math.pi * 4) + 4
                if (angle % 2 == 0):
                    dz = (touch.pos[1] - self.touch_pos[1])
                    self.z_pos = min(self.z_max, max(
                        0, self.tzpos + dz * 1.0))
                    self.axial_pos.text = " %s / %s " % (
                        self.z_pos, self.z_max)
                    self.dcmview1.set_z(self.z_pos)
                    self.dcmview2.set_z(self.z_pos)
                    self.display_image()
            else:
                pass

    def set_window(self):
        self.wcenter = int(self.wcenter)
        self.wwidth = int(self.wwidth)
        self.dcmview1.set_window(self.wcenter, self.wwidth)
        self.dcmview2.set_window(self.wcenter, self.wwidth)
        self.hu_width.text = str(self.wwidth)
        self.hu_center.text = str(self.wcenter)
        self.display_image()

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
#                #~ self.hu_center.text = str(self.wcenter)
#                #~ self.dcmview1.set_window(self.wcenter,self.wwidth)
#                #~ self.dcmview2.set_window(self.wcenter,self.wwidth)
#            #~ elif self.keypresses['ctrl'] or self.keypresses['rctrl']:
#                #~ self.wwidth += direction*speed*4
#                #~ self.wwidth = max(2,self.wwidth)
#                #~ self.hu_width.text = str(self.wwidth)
#                #~ self.dcmview1.set_window(self.wcenter,self.wwidth)
#                #~ self.dcmview2.set_window(self.wcenter,self.wwidth)
            self.z_pos = int(min(self.z_max, max(0, self.z_pos + direction * speed)))
            self.axial_pos.text = " %s / %s " % (self.z_pos, self.z_max)
            self.dcmview1.set_z(self.z_pos)
            self.dcmview2.set_z(self.z_pos)
            self.display_image()
            return True

    @gc_after
    def clear(self):
        self.dcmview1.clear()
        self.dcmview2.clear()
        for dirs in self.volumedirs:
            dirs.clear()
        del self.volumedirs[:]


class VGA(TaskScreen):

    def __init__(self, *args, **kwargs):
        super(VGA, self).__init__(*args, **kwargs)
        self.start_time = None

    def on_pre_leave(self, *args, **kwargs):
        leave_time = time.time()
        self.log('- VGA: "%s", @time: %.3f' %
                 (self.name, (leave_time - self.start_time)))
        self.log("")

    def on_button_press(self, *args, **kwargs):
        self.manager.current = self.manager.next()

    def set(self, *args, **kwargs):
        pass


class Question(TaskScreen):

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


class Choice(TaskScreen):

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


class Viewport(ScatterPlane):

    def __init__(self, **kwargs):
        kwargs.setdefault('size', (1920, 1080))
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('do_scale', False)
        kwargs.setdefault('do_translation', False)
        kwargs.setdefault('do_rotation', False)
        super(Viewport, self).__init__(**kwargs)
        Window.bind(system_size=self.on_window_resize)
        Clock.schedule_once(self.fit_to_window, -1)

    def on_window_resize(self, window, size):
        self.fit_to_window()

    def fit_to_window(self, *args):
        ratio = min(Window.width / float(self.width),
                    Window.height / float(self.height))
        self.scale = ratio
        if (self.width < self.height) == (Window.width < Window.height):  # portrait
            self.rotation = 0
        else:
            self.rotation = -90

        self.center = Window.center
        for c in self.children:
            c.size = self.size

    def add_widget(self, w, *args, **kwargs):
        super(Viewport, self).add_widget(w, *args, **kwargs)
        w.size = self.size


class InfoApp(App):

    scancode_dict = {
        67: 'f1',
        68: 'f2',
        69: 'f3',
        70: 'f4',
        71: 'f5',
        72: 'f6',
        73: 'f7',
        74: 'f8',
        75: 'f9',
        76: 'f10',
        95: 'f11',
        96: 'f12',
        278: 'home',
        279: 'end',
        277: 'ins',
        127: 'del'}

    def __init__(self, *args, **kwargs):
        super(InfoApp, self).__init__(*args, **kwargs)
        self.screen_dict = dict()

    def callback(self, *args, **kwargs):
        pass

    def on_start(self, *args, **kwargs):
        Window.bind(on_key_down=self.on_key_down)

    def screenshot(self, *args):
        pattern = "screenshot_{:03d}.png"
        directory = self.settings['screenshot_directory']
        i = 0
        if not os.path_exists(directory):
            return
        while os.path.exists(os.path.join(directory, pattern.format(i))):
            i += 1
        Window.screenshot(name=os.path.join(directory, pattern.format(i)))

    def on_key_down(self, win, key, scancode, string, modifiers):
        def key_match(scancode, modifiers, hotkey):
            parts = list(map(six.text_type.strip, hotkey.lower().split("+")))
            code = parts[-1]
            if six.text_type(self.scancode_dict.get(scancode, None)) != code:
                return False
            mods = set(parts[:-1])
            if len(mods ^ modifiers) > 0:
                return False
            return True

        if key_match(scancode, set(modifiers), six.text_type(self.settings["screenshot_hotkey"])):
            self.screenshot()
            return True

        if key_match(scancode, set(modifiers), six.text_type(self.settings["fullscreen_hotkey"])):
            win.toggle_fullscreen()
            for s in self.screens:
                s.canvas.ask_update()
            return True

    def build(self):

        self.screens = []
        self.sm = ScreenManager()
        self.volumecache = cachetools.LRUCache(maxsize=4)

        for idx, event in enumerate(self.events):
            if event.type == "END":
                screen = End(name="%s" % event.name)
            if event.type == "GOTO":
                screen = Goto(name="goto_%s" % idx)
                screen.label = event.name
            elif event.type == "INFO":
                screen = Choice(name="%s" % event.name)
            elif event.type == "CHOICE":
                screen = Choice(name="%s" % event.name)
            elif event.type == "QUESTION":
                screen = Question(name="%s" % event.name)
            elif event.type == "VGA":
                screen = VGA(name="%s" % event.name)
            elif event.type == "PAIR":
                screen = Pair(name="%s" % event.name)

            screen.automated_test = self.automated_test
            screen.var = dict()
            var = screen.var
            screen.global_settings = self.settings
            screen.contents = self.contents
            screen.type = event.type
            self.sm.add_widget(screen)
            self.screens.append(screen)
            var.update(self.settings)
            for kv in event.keyvalue:
                if len(kv.value) == 1:
                    var[kv.key] = kv.value[0]
                elif len(kv.value) == 0:
                    var[kv.key] = None
                else:
                    var[kv.key] = kv.value

            if event.type == "END":
                continue

            if event.type == "GOTO":
                continue

            if event.type == "INFO":
                screen.add_options((var.get('button', 'Next'),))

            if event.type == "CHOICE":
                screen.add_options(screen.var['options'])
                screen.add_conditionals(event.branch)

            if event.type == "QUESTION":
                screen.add_questions(event.question)

            if event.type == "VGA":
                pass

            if event.type == "PAIR":
                screen.add_questions(KV(event.keyvalue, "question"))
                screen.add_dirs(
                    KV(event.keyvalue, "random_pairs"), self.volumecache)
                screen.add_options(screen.var['options'])

            if 'text' in var:
                src = var['text'][1:-1]
                if src in self.contents:
                    screen.document.text = self.contents[src]
                else:
                    if os.path.exists(src):
                        screen.document.source = src
                    else:
                        screen.document.text = "File not found: %s " % src

        screen = End(name="automatic exit point")
        self.sm.add_widget(screen)
        self.screens.append(screen)
        self.screen_dict[screen.name] = screen
        for s in self.screens:
            s.log = self.logger

        self.logger(
            "------------------------------------------------------------------")
        self.logger("<General>")
        t = time.time()
        d = datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
        self.logger('  date = "%s"' % d)
        self.logger('  timestamp = %s' % t)
        if var['random_seed'] == "time":
            seed = int(time.time())
        else:
            seed = int(var['random_seed'])
        self.logger('  random_seed = %s' % seed)
        random.seed(seed)
        self.logger("")
        self.logger("<Timeline>")
        self.logger("")

        self.viewport = Viewport(size=(1920, 1080))
        self.viewport.add_widget(self.sm)
        return self.viewport


def run(*argv):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    travis = 'TRAVIS' in os.environ
    if not travis:
        if len(argv) != 2:
            print("Usage: PerceptionMD STUDY_DESCRIPTION_FILE")
            sys.exit(1)

        if argv[1] == "example":
            filename = os.path.join(dir_path, "unittests/travis-example.pmd")
        else:
            if not os.path.exists(argv[1]):
                print("Usage: PerceptionMD STUDY_DESCRIPTION_FILE")
                print("Note: the file must exist and readable!")
                sys.exit(1)
            filename = argv[1]
    else:
        filename = os.path.join(dir_path, "unittests/travis-example.pmd")

    import kivy
    kivy.require('1.8.0')
    Config.set('kivy', 'desktop', '1')
    Config.set('kivy', 'loglevel', 'error')
    Config.set('kivy', 'exit_on_escape', '1')
    Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

    langfile = os.path.join(dir_path, 'lang', 'perception.tx')
    explang_mm = textx.metamodel.metamodel_from_file(langfile)
    model = explang_mm.model_from_file(filename)

    # Parsing global settings
    contents = dict()
    settings = dict()

    settings.update(default_settings)
    for content in model.contents:
        k = content.name[1:-1]
        v = content.content
        contents[k] = v

    for kv in model.settings.keyvalue:
        k, v = kv.key, kv.value
        if len(v) == 1:
            settings[k] = v[0]
        elif len(v) == 0:
            settings[k] = None
        else:
            settings[k] = v

    # Building application and its window
    Builder.load_file(os.path.join(dir_path, "widgets/infoscreen.kv"))
    Window.size = (int(settings['window_width']),
                   int(settings['window_height']))
    Window.fullscreen = settings['full_screen'] != 0

    os.chdir(os.path.dirname(filename))
    app = InfoApp()
    app.contents = contents
    app.settings = settings
    app.logger = Logger(settings['logfile'])
    app.events = model.timeline.events
    app.automated_test = travis
    if travis:
        print("Travis test run")
    app.run()

if __name__ == '__main__':
    if six.PY2:
        run(*[unicode(x, 'utf-8') for x in sys.argv])
    else:
        run(*sys.argv)
