#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import numpy as np

from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, ListProperty
from kivy.graphics.texture import Texture
from perceptionmd.utils import gc_after
import perceptionmd.utils as utils

class DICOMView(BoxLayout):

    def __init__(self, *args, **kwargs):
        super(DICOMView, self).__init__(**kwargs)
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
