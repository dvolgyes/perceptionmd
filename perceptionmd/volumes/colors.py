#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals
from matplotlib.colors import LinearSegmentedColormap as LS_Colormap
import matplotlib.pyplot as plt
import os
import numpy as np


def create_colormap(name, cmap):
    if not os.path.exists(cmap):
        return plt.cm.get_cmap(cmap)
    array = np.clip(np.fromfile(cmap, sep=' ').reshape(-1, 3), 0, 255) / 255.0
    return LS_Colormap.from_list(name, array.tolist(), array.shape[0])
