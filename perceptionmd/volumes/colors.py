#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
import os

def create_colormap(name, cmap):
    if os.path.exists(cmap):
        array = np.clip(np.fromfile(cmap, sep=" ").reshape(-1, 3), 0, 255) / 255.0
        return LinearSegmentedColormap.from_list(name, array.tolist(), array.shape[0])
    try:
        return plt.cm.get_cmap(cmap)
    except:
        pass
    return plt.cm.gray
