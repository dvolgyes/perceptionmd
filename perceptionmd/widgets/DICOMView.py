#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import numpy as np

from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, BooleanProperty, ListProperty, BoundedNumericProperty, NumericProperty
from kivy.graphics.texture import Texture
from perceptionmd.utils import gc_after
import perceptionmd.utils as utils
from kivy.clock import Clock
from functools import partial
from collections import defaultdict


class DICOMView(BoxLayout):
    axis = NumericProperty(0)
    base_axis = NumericProperty(0)
    rotate = NumericProperty(0)
    alpha = BoundedNumericProperty(1.0, min=0.0, max=1.0)
    wcenter = NumericProperty(0)
    wwidth = NumericProperty(100)
    z_pos = NumericProperty(0)
    z_max = NumericProperty(0)
    base_wcenter = NumericProperty(0)
    base_wwidth = NumericProperty(100)
    rel = ListProperty([0, 0])
    base_rotate = NumericProperty(0)
    colormap = ObjectProperty(None)
    base_colormap = ObjectProperty(None)
    initialized = BooleanProperty(False)
    flips = ListProperty([False, False, False])
    base_flips = ListProperty([False, False, False])
    base_layer = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        super(DICOMView, self).__init__(*args, **kwargs)
        self.mainw = None
        self.dcm_image = None
        self.core_volume = None
        self.base_core_volume = None
        self.base_volume = None
        self.empty = np.zeros(shape=(512, 512), dtype=np.uint8)
        self.black = np.ones(shape=(1, 512, 512), dtype=np.float32) * -32000
        self.array = np.zeros(shape=(1, 512, 512), dtype=np.uint8)
        self.volume = np.zeros(shape=(1, 512, 512), dtype=np.uint8)
        self.img_texture = Texture.create(size=(512, 512))
        self.base_img_texture = Texture.create(size=(512, 512))
        self.volume = np.zeros(shape=(1, 512, 512), dtype=np.uint8)
        self.core_volume = self.volume
        self.display_on_trigger = Clock.create_trigger(partial(self.display_image_trigger, True))
        self.display_off_trigger = Clock.create_trigger(partial(self.display_image_trigger, False))

    @gc_after
    def clear(self):
        self.set_dummy_volume()
        self.set_dummy_volume(base_volume=True)

    def set_volume(self, volmeta, base_layer=False):
        (volume, meta) = volmeta
        if base_layer:
            self.base_core_volume = volume
            self.base_volume = volume
        else:
            self.core_volume = volume
            self.volume = volume
        self.orient_volume()

    def on_z_max(self, *args, **kwargs):
        self.z_pos = min(self.z_pos, self.z_max)

    def on_z_pos(self, *args, **kwargs):
        self.z_pos = int(max(0, min(self.z_max, self.z_pos)))

    def on_alpha(self, *args):
        self.dcm_image.opacity = self.alpha

    def on_initialized(self, *args, **kwargs):
        self.dcm_image.texture = self.img_texture
        self.base_image.texture = self.base_img_texture
        self.blit(self.empty, colorfmt='luminance', base_layer=True)
        self.blit(self.empty, colorfmt='luminance')

    def orient_volume(self):
        self.volume = self.core_volume
        self.base_volume = self.base_core_volume
        if self.axis > 0:
            self.volume = np.swapaxes(self.volume, 0, self.axis)
        if self.rotate > 0:
            t = np.swapaxes(self.volume, 0, 2)
            t = np.rot90(t, k=int(self.rotate))
            self.volume = np.swapaxes(t, 0, 2)
        if self.flips[0]:
            self.volume = self.volume[::-1, ...]
        if self.flips[1]:
            self.volume = self.volume[:, ::-1, ...]
        if self.flips[2]:
            self.volume = self.volume[..., ::-1]
        if self.base_volume is not None:
            if self.base_axis > 0:
                self.base_volume = np.swapaxes(self.base_volume, 0, self.base_axis)
            if self.base_rotate > 0:
                t = np.swapaxes(self.base_volume, 0, 2)
                t = np.rot90(t, k=self.base_rotate)
                self.base_volume = np.swapaxes(t, 0, 2)
            if self.base_flips[0]:
                self.base_volume = self.base_volume[::-1, ...]
            if self.base_flips[1]:
                self.base_volume = self.base_volume[:, ::-1, ...]
            if self.base_flips[2]:
                self.base_volume = self.base_volume[..., ::-1]
        self.z_max = self.volume.shape[0] - 1

    def set_dummy_volume(self, base_volume=False):
        self.set_volume((self.black.reshape(1, 512, 512), defaultdict(lambda: None)), base_volume)

    def on_scroll(self, touch, rel):  # pragma: no cover
        return None

    def blit(self, image, colorfmt='rgba', bufferfmt='ubyte', base_layer=False):
        if base_layer:
            if self.base_image.texture.size != image.shape[0:2]:
                self.base_image.texture = Texture.create(image.shape[0:2])
                self.empty = np.zeros(shape=self.base_image.texture.size[0:2], dtype=np.uint8)
            self.base_image.texture.blit_buffer(image.ravel(), colorfmt=colorfmt, bufferfmt=bufferfmt)
        else:
            if self.dcm_image.texture.size != image.shape[0:2]:
                self.dcm_image.texture = Texture.create(image.shape[0:2])
                self.empty = np.zeros(shape=self.dcm_image.texture.size[0:2], dtype=np.uint8)
            self.dcm_image.texture.blit_buffer(image.ravel(), colorfmt=colorfmt, bufferfmt=bufferfmt)

    def display_image(self, show=True):
        if show:
            self.display_on_trigger()
        else:
            self.display_off_trigger()

    def display_image_trigger(self, show=True, *args):
        self.initialized = True
        if show:
            shift = self.wcenter - self.wwidth / 2.0
            array = np.clip((self.volume[self.z_pos, ...] - shift) / (self.wwidth / 255.0), 0, 255).astype(np.uint8)
            if array.shape[0] != array.shape[1]:
                array = utils.padding_square(np.clip(array, 0, 255).astype(np.uint8))
            if self.colormap is not None:
                slice_str = (self.colormap(array) * 255).astype(np.uint8)
                self.blit(slice_str.reshape(array.shape + (-1,)))
            else:
                self.blit(array, colorfmt='luminance')
            if self.base_volume is not None:
                shift = self.base_wcenter - self.base_wwidth / 2.0
                array = np.clip(
                    (self.base_volume[self.z_pos, ...] - shift) / (self.base_wwidth / 255.0), 0, 255).astype(np.uint8)
                if array.shape[0] != array.shape[1]:
                    array = utils.padding_square(np.clip(array, 0, 255).astype(np.uint8))
                if self.base_colormap is not None:
                    slice_str = (self.base_colormap(array) * 255).astype(np.uint8).reshape(array.shape + (-1,))
                    self.blit(slice_str, base_layer=True)
                else:
                    self.blit(array, colorfmt='luminance', base_layer=True)
        else:
            self.blit(self.empty, colorfmt='luminance', base_layer=True)
            self.blit(self.empty, colorfmt='luminance')
        self.dcm_image.canvas.ask_update()
        self.canvas.ask_update()
