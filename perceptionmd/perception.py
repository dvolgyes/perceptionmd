#!/usr/bin/python2
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

try:   # pragma: no cover
    import gi
    gi.require_version('Gtk', '3.0')
except:
    pass  # no GTK is installed

import sys
import os
import time
import datetime
import random
import cachetools
import six
from collections import defaultdict
import numpy as np

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.config import Config

import textx
import textx.metamodel

from perceptionmd.widgets import ViewPort, Goto, End, Choice, Question, Pairwise, VGA
from perceptionmd.defaults import default_settings
from perceptionmd.utils import Logger, listify


class PerceptionMDApp(App):

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
        super(PerceptionMDApp, self).__init__(*args, **kwargs)
        self.screen_dict = dict()
        self.winsize = Window.size

    def on_start(self, *args, **kwargs):
        Window.bind(on_key_down=self.on_key_down)

    def screenshot(self, *args):
        pattern = "screenshot_{:03d}.png"
        directory = self.settings['screenshot_directory']
        i = 0
        if not os.path.exists(directory):
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
            if not Window.fullscreen:
                self.winsize = Window.size
                Window.size = (int(self.settings['window_width']), int(self.settings['window_height']))
            else:
                Window.size = self.winsize
            if not self.automated_test:
                Window.fullscreen ^= True
            self.viewport.fit_to_window()
            for s in self.screens:
                s.canvas.ask_update()
            return True

    def build(self):

        self.screens = []
        self.sm = ScreenManager()
        self.volumecache = cachetools.LRUCache(maxsize=4)

        for idx, event in enumerate(self.events):
            if event.type == "END":
                screen = End.End(name="%s" % event.name)
            if event.type == "GOTO":
                screen = Goto.Goto(name="goto_%s" % idx)
                screen.label = event.name
            elif event.type == "INFO":
                screen = Choice.Choice(name="%s" % event.name)
            elif event.type == "CHOICE":
                screen = Choice.Choice(name="%s" % event.name)
            elif event.type == "QUESTION":
                screen = Question.Question(name="%s" % event.name)
            elif event.type == "VGA":
                screen = VGA.VGA(name="%s" % event.name) # pragma: no cover
            elif event.type == "PAIR":
                screen = Pairwise.Pairwise(name="%s" % event.name)
            elif event.type == "REFERENCE":
                screen = Pairwise.Pairwise(name="%s" % event.name)
                screen.reference = True

            screen.automated_test = self.automated_test
            screen.var = defaultdict(list)
            var = screen.var
            screen.global_settings = self.settings
            screen.contents = self.contents
            screen.type = event.type
            self.sm.add_widget(screen)
            self.screens.append(screen)
            var.update(self.settings)
            repeated_keys = defaultdict(int)
            for kv in event.keyvalue:
                repeated_keys[kv.key] += 1

            for kv in event.keyvalue:
                rep = repeated_keys[kv.key] > 1
                if len(kv.value) == 1:
                    val = kv.value[0]
                elif len(kv.value) == 0:
                    val = None
                else:
                    val = kv.value
                if rep:
                    var[kv.key].append(val)
                else:
                    var[kv.key] = val

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
                screen.questions = event.question
                screen.ratio = var['text_input_ratio']
            if event.type == "VGA": # pragma: no cover
                pass

            if event.type in ["PAIR", "REFERENCE"]:
                screen.add_questions(listify(screen.var['question']))
                screen.add_dirs(listify(screen.var['random_pairs']), self.volumecache)
                screen.add_dirs(listify(screen.var['base_layer']), self.volumecache, base_layer=True)
                screen.add_options(screen.var['options'])

            if event.type in ["VGA"]: # pragma: no cover
                screen.add_dirs(listify(screen.var['random_volumes']), self.volumecache)
                screen.add_dirs(listify(screen.var['base_layer']), self.volumecache, base_layer=True)
                screen.add_questions(listify(screen.var['question']), screen.var['options'])

            if 'text' in var:
                src = var['text'][1:-1]
                if src in self.contents:
                    screen.document.text = self.contents[src]
                else:
                    if os.path.exists(src):
                        screen.document.source = src

        screen = End.End(name="automatic exit point")
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
        np.random.seed(seed)
        self.logger("")
        self.logger("<Timeline>")
        self.logger("")

        self.viewport = ViewPort.Viewport(
            size=(int(self.settings['window_width']),
                  int(self.settings['window_height'])))
        self.viewport.add_widget(self.sm)
        return self.viewport


def run(*argv):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    continuous_integration = os.environ.get('CI', 'false') != 'false'
    if not continuous_integration: # pragma: no cover
        if len(argv) != 2:
            print("Usage: PerceptionMD STUDY_DESCRIPTION_FILE")
            sys.exit(1)

        if argv[1] == "example":
            filename = os.path.join(dir_path, "examples/simple/simple.pmd")
        else:
            if not os.path.exists(argv[1]):
                print("Usage: PerceptionMD STUDY_DESCRIPTION_FILE")
                print("Note: the file must exist and readable!")
                sys.exit(1)
            filename = os.path.abspath(argv[1])
    else:
        if len(argv) != 2:
            filename = os.path.join(dir_path, "unittests/travis-example.pmd")
        else:
            filename = sys.argv[1]

    import kivy
    kivy.require('1.8.0')
    Config.set('kivy', 'desktop', '1')
    Config.set('kivy', 'loglevel', 'error')
    Config.set('kivy', 'exit_on_escape', '1')
    Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
    Config.set('graphics', 'fullscreen', 'auto')

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
    Builder.load_file(os.path.join(dir_path, "widgets/ComboButtons.kv"))
    Builder.load_file(os.path.join(dir_path, "widgets/infoscreen.kv"))
    Window.size = (int(settings['window_width']),
                   int(settings['window_height']))
    Window.fullscreen = settings['fullscreen'] != 0

    os.chdir(os.path.dirname(filename))
    app = PerceptionMDApp()
    app.contents = contents
    app.settings = settings
    app.logger = Logger(settings['logfile'])
    app.events = model.timeline.events
    app.automated_test = continuous_integration
    if continuous_integration:
        print("Continuous integration: test run")
    app.run()

if __name__ == '__main__': # pragma: no cover
    if six.PY2:
        run(*[unicode(x, 'utf-8') for x in sys.argv])
    else:
        run(*sys.argv)
