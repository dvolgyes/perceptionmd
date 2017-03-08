#!/usr/bin/python2
from __future__ import print_function, division, absolute_import

import sys, os, time, datetime
import numpy as np
import random
import itertools
from collections import defaultdict

from textx.metamodel import metamodel_from_file

import gi
gi.require_version('Gtk', '3.0')

import kivy
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
import CTTools
import CTTools.DCM
import threading
import gc
from matplotlib.colors import LinearSegmentedColormap

def create_color_map(name,filename=None,array=None):
    if filename is not None:
        array = np.clip(np.fromfile(filename,sep=" ").reshape(-1,3),0,255) / 255.0
    return LinearSegmentedColormap.from_list(name,array.tolist(),array.shape[0])

def gc_collect(func):
    def func_wrapper(*args,**kwargs):
       result = func(*args,**kwargs)
       gc.collect()
       return result
    return func_wrapper

def KV(kvs,key):
    for kv in kvs:
        if kv.key==key:
            return kv.value
    return None

def random_combinations(lst,count=2):
    result = []
    comb = list(itertools.combinations(lst,count))
    random.shuffle(comb)
    for c in comb:
        v = c if random.randint(0,1)==0 else c[::-1]
        result.append(v)
    return result

class DICOMVIEW(BoxLayout):
    def __init__(self, *args, **kwargs):
        super(DICOMVIEW, self).__init__(**kwargs)
        self.mainw = None
        self.dcm_image = ObjectProperty(None)
        self.rel = ListProperty( [0,0] )
        self.empty = np.zeros(shape=(512, 512), dtype=np.uint8)
        self.array = np.zeros(shape=(1,512, 512), dtype=np.uint8)
        self.volume = np.zeros(shape=(1,512, 512), dtype=np.uint8)
        self.z_pos = 0
        self.z_max = 0
        self.img_texture = Texture.create(size=(512,512))
        self.wcenter = 0
        self.wwidth = 100
        self.initialized = False
        self.colormap = None

    def set_colormap(self,cmap):
        self.colormap = cmap
        self.set_window(self.wcenter,self.wwidth)

    def set_volume(self, volume):
        self.volume = volume
        self.z_max = volume.shape[0]-1
        self.set_z(0)
        self.set_window(self.wcenter,self.wwidth)

    def set_window(self,center,width):
        gc.collect()
        self.wcenter = center
        self.wwidth = width
        self.array = (self.volume - self.wcenter)/self.wwidth*2.0+1
        self.array = np.clip(self.array * 255,0,255).astype(np.uint8)
        #~ if self.colormap is not None:
            #~ self.array = (self.colormap(self.array)*255).astype(np.uint8)
        gc.collect()

    def set_z(self,z):
        new_z = int(max(0,min(self.z_max,z)))
        if new_z != self.z_pos:
            self.z_pos = new_z
            self.display_image()

    def on_scroll(self, touch, rel):
        return None

    def display_image(self,show=True):
        if not self.initialized:
            self.dcm_image.texture=self.img_texture
            self.initialized = True
            self.dcm_image.texture.blit_buffer(self.empty.tostring(), colorfmt='luminance', bufferfmt='ubyte')
        if show:
            if self.colormap is not None:
                slice_str = (self.colormap(self.array[self.z_pos,:,:])*255).astype(np.uint8).tostring()
                self.dcm_image.texture.blit_buffer(slice_str, colorfmt='rgba', bufferfmt='ubyte')
            else:
                self.dcm_image.texture.blit_buffer(self.array[self.z_pos,:,:].tostring(), colorfmt='luminance', bufferfmt='ubyte')
        else:
            self.dcm_image.texture.blit_buffer((self.empty).tostring(), colorfmt='luminance', bufferfmt='ubyte')

        #~ self.dcm_image.texture.ask_update()
        self.dcm_image.canvas.ask_update()
        self.canvas.ask_update()


class Logger():

    def __init__(self, filename):
        self.filename = filename
        with open(self.filename, "a+"):
            pass

    def append(self, line):
        with open(self.filename, "a") as f:
            f.write(line.rstrip())
            f.write("\n")

    def __call__(self,argument):
        self.append(argument)

class TaskScreen(Screen):
    def __init__(self,*args,**kwargs):
        super(TaskScreen, self).__init__(*args,**kwargs)
        self.start_time = None

    def on_button_press(self, *args, **kwargs):
        self.manager.current = self.manager.next()

    def on_enter(self,*args,**kwargs):
        self.start_time = time.time()

class Goto(Screen):
    def __init__(self,*args,**kwargs):
        super(Goto, self).__init__(*args,**kwargs)

    def on_enter(self):
        self.manager.current = self.label

    def set(self,label):
        self.label = label


class End(Screen):
    def __init__(self,*args,**kwargs):
        super(End, self).__init__(*args,**kwargs)

    def on_pre_enter(self):
        App.get_running_app().stop()

    def set(self,*args,**kwargs):
        pass

class Info(TaskScreen):
    def __init__(self,*args,**kwargs):
        super(Info, self).__init__(*args,**kwargs)
        self.start_time = None

    def set(self,*args,**kwargs):
        self.button.height = self.var['button_size']
        self.button.font_size = self.var['button_font_size']
        color = self.var['button_background_color']
        if color != "None":
            self.button.background_color =  color
            self.button.background_normal =""

        color = self.var['button_font_color']
        if color != "None":
            self.button.color = color

        color = self.var['background_color']
        if color != "None":
            self.document.background_color = color
        self.document.font_color = self.var['background_color']
        self.document.base_font_size = int(self.var['title_font_size'])

    def on_pre_leave(self, *args, **kwargs):
        leave_time = time.time()
        self.log('- INFO: "%s", @time: %.3f' % (self.name , (leave_time - self.start_time)))
        self.log("")


class Pair(Screen):

    def __init__(self,*args,**kwargs):
        super(Pair, self).__init__(**kwargs)
        self.start_time = None
        self.total_time = 0
        self.wall_time = None
        self.dicomdirs = []
        self.serieses = []
        self.loglines = []
        self.texts = []
        self.sources = []
        self.choice_label = dict()
        self.choice_idx = dict()
        self.current_task_idx = -1
        self.lock = threading.Lock()
        #~ self.volume = []
        #~ self.array = [(np.random.random((512, 512)) * 255).astype(np.uint8),(np.random.random((512, 512)) * 255).astype(np.uint8)]
        #~ self.img_texture = [Texture.create(size=(512,512)),Texture.create(size=(512,512))]

        self.black = None
        self.z_pos = 0
        self.z_max = 0
        self.wwidth = 600
        self.wcenter = 200
        #~ self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
        self.keypresses = defaultdict(lambda : False)

    def add_dirs(self,dirs):
        for s,d in enumerate(dirs):
            self.serieses.append(dict())
            dicomdir=CTTools.DCM.DICOMDIR()
            dicomdir.find_dicoms(d[1:-1])
            self.loglines.append("    dicom-set %s:" % s)
            for idx,series in enumerate(dicomdir.series_iterator()):
                directory = os.path.dirname(dicomdir._files[series][-1][1])
                desc = dicomdir._texts[series]
                self.serieses[-1][idx] = (series,directory)
                self.loglines.append('        volume %s: "%s" ("%s")' % (idx,directory,desc))
            self.dicomdirs.append(dicomdir)

    def add_questions(self,questions):
        for question in questions:
            self.sources.append(question)
            src = question[1:-1]
            if src in contents:
                text = contents[src]
            else:
                if os.path.exists(src):
                    with open(src,"rt") as f:
                        text = f.read()
                else:
                        text = "File not found: %s " % src
            self.texts.append(text)

    def generate(self):
        result = []
        for qidx,question in enumerate(self.texts):
            taskl = []
            for vidx,series in enumerate(self.serieses):
                for pair in random_combinations(series):
                    task = (qidx, vidx, pair)
                    taskl.append(task)
            random.shuffle(taskl)
            result.extend(taskl)
        self.tasklist = result
        self.loglines.append("    results:")
        self.loglines.append("        question, set, left, right, answer, answer text, @time")
        self.next()
        self.update_scene()
        return result

    def next(self):
        self.current_task_idx += 1
        if self.current_task_idx>= len(self.tasklist):
            return False
        return True

    def update_scene(self,*args,**kwargs):
        self.disable_buttons()
        self.document.text = "Please wait for the next volumes..."
        self.axial_pos.text = " N/A "
        self.display_image(False)
        self.canvas.ask_update()
        self.update_thread = threading.Thread(target=self.up)
        self.update_thread.start()

    def up(self):
        with self.lock:
            task = self.tasklist[self.current_task_idx]
            (question,selected_set, (volID1,volID2)) = task
            series1 = self.serieses[selected_set][volID1][0]
            series2 = self.serieses[selected_set][volID2][0]

            self.dcmview1.set_volume(self.dicomdirs[selected_set].volume(series1))
            self.dcmview2.set_volume(self.dicomdirs[selected_set].volume(series2))

            self.dcmview1.set_window(self.wcenter,self.wwidth)
            self.dcmview2.set_window(self.wcenter,self.wwidth)
            self.z_max = self.dcmview1.z_max
            self.z_pos = self.z_max // 2
            self.axial_pos.text = " %s / %s " % (self.z_pos,self.z_max)
            self.hu_center = str(self.wcenter)
            self.hu_width = str(self.wwidth)

            self.dcmview1.set_z(self.z_pos)
            self.dcmview2.set_z(self.z_pos)
            #~ self.document.text = ("Q%s, task #%s " % (question+1,self.current_task_idx+1))+self.texts[question]
            self.document.text = self.texts[question]
            #~ self.display_image(True)
            #~ self.dcmview1.canvas.ask_update()
            #~ self.dcmview2.canvas.ask_update()
            #~ self.canvas.ask_update()
            self.enable_buttons()
            self.start_time = time.time()
            Clock.schedule_once(self.display_image)
            if len(self.tasklist)+1<self.current_task_idx:
                nexttask = self.tasklist[self.current_task_idx+1]
                (next_question,next_selected_set, (next_volID1,next_volID2)) = nexttask
                next_series1 = self.serieses[next_selected_set][next_volID1][0]
                next_series2 = self.serieses[next_selected_set][next_volID2][0]
                self.dicomdirs[next_selected_set].preload_volumes(next_series1)
                self.dicomdirs[next_selected_set].preload_volumes(next_series2)


        #~ def gen_image(self, obj):
            #~ array = self.array
            #~ self.img_texture.blit_buffer(
                #~ array.tostring(), colorfmt='luminance', bufferfmt='ubyte')
            #~ if self.first:
                #~ self.dcm_image.texture = self.img_texture
                #~ self.first = False
            #~ self.dcm_image.texture = self.img_texture
            #~ self.canvas.ask_update()

    def disable_buttons(self):
        for button in self.choice_idx:
            button.disabled = True
            button.canvas.ask_update()

    def enable_buttons(self):
        for button in self.choice_idx:
            button.disabled = False
            button.canvas.ask_update()


    def display_image(self,show=True):
        self.dcmview1.display_image(show)
        self.dcmview2.display_image(show)

    def on_enter(self,*args,**kwargs):
        self.set()
        print("on enter")
        self.wall_time = time.time()
        self.start_time = time.time()
        #~ self._keyboard.bind(on_key_down=self._on_keyboard_down)
        #~ self._keyboard.bind(on_key_up=self._on_keyboard_up)

    def on_pre_leave(self, *args, **kwargs):
        #~ self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        #~ self._keyboard.unbind(on_key_up=self._on_keyboard_up)

        leave_time = time.time()
        self.log('- PAIR: "%s", @time: %.3f @effective_time: %.3f ' % (self.name , leave_time - self.wall_time,self.total_time))
        for l in self.loglines:
            self.log(l)
        self.loglines=[]
        self.log("")

    #~ def on_button_press(self, *args, **kwargs):
        #~ self.manager.current = self.manager.next()

    def on_button(self,button,*args,**kwargs):
        print("ONBUTTON")
        now = time.time()
        i=self.choice_idx[button]
        task = self.tasklist[self.current_task_idx]
        elapsed = (now -self.start_time)
        self.total_time += elapsed
                                      #~ question,set,left,right,answer
        self.loglines.append('        {:^8},{:^4},{:^5},{:^6},{:^7},{:^12}, {:.3f}'.format(task[0],task[1],task[2][0],task[2][1],i,self.choice_label[i],elapsed))
        print("Selection",i,self.choice_label[i])
        #~ self.manager.current = self.manager.next()
            # save current selection
        if not self.next():
            self.manager.current = self.manager.next()
        else:
            self.update_scene()
        #~ else:
            #~ # set up new scene
            #~ pass

    def set(self,*args,**kwargs):
        self.generate()

    def _keyboard_closed(self):
        pass
        #~ print('My keyboard have been closed!')
        #~ self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        #~ self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        print('The key', keycode, 'have been pressed')
        print(' - text is %r' % text)
        print(' - modifiers are %r' % modifiers)
        self.keypresses[keycode[1]] = True

        # Keycode is composed of an integer + a string
        # If we hit escape, release the keyboard
        if keycode[1] == 'escape':
            keyboard.release()

        # Return True to accept the key. Otherwise, it will be used by
        # the system.
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
                    b.on_touch_down(touch)
                #~ touch.grab(self)
                #~ print(touch)

    #~ def on_touch_move(self, touch):
        #~ if touch.grab_current is self:
            #~ pass
            #~ # I received my grabbed touch
        #~ else:
            #~ # it's a normal touch
            #~ pass

    #~ def on_touch_up(self, touch):
        #~ if touch.grab_current is self:
            #~ touch.ungrab(self)
        #~ else:
            #~ pass

    def on_scroll(self,direction):
        with self.lock:
            if self.keypresses['shift']:
                self.wcenter += direction
                self.dcmview1.set_window(self.wcenter,self.wwidth)
                self.dcmview2.set_window(self.wcenter,self.wwidth)
                self.display_image()
                return True
            elif self.keypresses['ctrl']:
                self.wwidth += direction
                self.dcmview1.set_window(self.wcenter,self.wwidth)
                self.dcmview2.set_window(self.wcenter,self.wwidth)
                self.display_image()
                return True
            else:
                self.z_pos = min(self.z_max,max(0,self.z_pos + direction))
                self.axial_pos.text = " %s / %s " % (self.z_pos,self.z_max)
                self.dcmview1.set_z(self.z_pos)
                self.dcmview2.set_z(self.z_pos)
            self.display_image()
            return True


class VGA(Screen):
    def __init__(self,*args,**kwargs):
        super(VGA, self).__init__(*args,**kwargs)
        self.start_time = None

    def on_enter(self,*args,**kwargs):
        self.start_time = time.time()

    def on_pre_leave(self, *args, **kwargs):
        leave_time = time.time()
        self.log('- VGA: "%s", @time: %.3f' % (self.name , (leave_time - self.start_time)))
        self.log("")

    def on_button_press(self, *args, **kwargs):
        self.manager.current = self.manager.next()

    def set(self,*args,**kwargs):
        pass

class Question(Screen):

    def __init__(self,*args,**kwargs):
        super(Question, self).__init__(*args,**kwargs)
        self.questions = []
        self.variables = dict()
        self.start_time = None

    def set(self,*args,**kwargs):
        pass

    def add_questions(self, qs):
        for q in qs:
            label = Label(text=q.message)
            input = TextInput()
            label.font_size = self.var['input_label_font_size']
            input.font_size = self.var['input_field_font_size']
            self.variables[q.variable] = (input,q.type)
            self.layout.add_widget(label)
            self.layout.add_widget(input)
        self.button.height = self.var['button_size']
        self.button.font_size = self.var['button_font_size']


    def on_enter(self,*args,**kwargs):
        self.start_time = time.time()

    def on_pre_leave(self, *args, **kwargs):
        leave_time = time.time()
        self.log('- QUESTION: "%s", @time: %.3f' % (self.name , (leave_time - self.start_time)))
        for key in self.variables:
            value = self.variables[key][0].text
            field_type = self.variables[key][1]
            self.variables[key] = value
            if field_type == "STRING":
                self.log('    {:<10} = "{}"' .format(key,value))
            else:
                if len(value)==0:
                    value=0
                self.log('    {:<10} = {}' .format(key,value))

        self.log("")

    def on_button_press(self, *args, **kwargs):
        self.manager.current = self.manager.next()


class Choice(Screen):
    def __init__(self,*args,**kwargs):
        super(Choice, self).__init__(*args,**kwargs)
        self.conditions = dict()
        self.choice_label = dict()
        self.names_to_screen = dict()
        self.start_time = None

    def on_enter(self,*args,**kwargs):
        self.start_time = time.time()

    def on_pre_leave(self, *args, **kwargs):
        leave_time = time.time()
        self.log('- CHOICE: "%s", @time: %.3f' % (self.name , (leave_time - self.start_time)))
        self.log('    {:<10} = {}' .format("selection",self.choice))
        self.log('    {:<10} = {}' .format("label",self.choice_label[self.choice]))
        self.log("")

    def on_button(self, button):
        self.choice, key = self.buttons[button]
        if key in self.conditions:
            self.manager.current = self.conditions[key]
        else:
            self.manager.current = self.manager.next()

    def add_conditionals(self, lst):
        for item in lst:
            self.conditions[item.condition] = item.consequence

    def set(self,*args,**kwargs):
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

class InfoApp(App):
    def __init__(self,*args,**kwargs):
        super(InfoApp, self).__init__(*args,**kwargs)

    def callback(self, *args, **kwargs):
        print(args)
        print(kwargs)

    def build(self):
        self.screens = []
        self.sm = ScreenManager()
        for idx, event in enumerate(self.events):
            if event.type == "END": screen = End(name="%s" % event.name)
            if event.type == "GOTO":
                screen = Goto(name="goto_%s" % idx)
                screen.set(event.name)
            elif event.type == "INFO": screen = Info(name="%s" % event.name)
            elif event.type == "CHOICE": screen = Choice(name="%s" % event.name)
            elif event.type == "QUESTION": screen = Question(name="%s" % event.name)
            elif event.type == "VGA": screen = VGA(name="%s" % event.name)
            elif event.type == "PAIR": screen = Pair(name="%s" % event.name)

            screen.var = dict()
            var = screen.var
            screen.local_settings = event
            screen.global_settings = self.settings
            screen.type = event.type
            self.sm.add_widget(screen)
            self.screens.append(screen)
            var.update(self.settings)
            for kv in event.keyvalue:
                if len(kv.value) == 1:
                    var[kv.key]=kv.value[0]
                elif len(kv.value) == 0:
                    var[kv.key] = None
                else:
                    var[kv.key]=kv.value

            if event.type == "END":
                continue

            if event.type == "GOTO":
                continue

            if event.type == "INFO":
                if 'button' in var:
                    screen.button.text = var['button']
                pass

            if event.type == "CHOICE":
                screen.add_options(screen.var['options'])
                screen.add_conditionals(event.branch)
                pass

            if event.type == "QUESTION":
                screen.add_questions(event.question)
                pass

            if event.type == "VGA":
                pass

            if event.type == "PAIR":
                screen.add_questions(KV(event.keyvalue,"question"))
                screen.add_dirs(KV(event.keyvalue,"random_pairs"))
                screen.add_options(screen.var['options'])

            if 'text' in var:
                src = var['text'][1:-1]
                if src in contents:
                    screen.document.text = contents[src]
                else:
                    if os.path.exists(src):
                        screen.document.source = src
                    else:
                        screen.document.text = "File not found: %s " % src

        screen = End(name="automatic exit point")
        self.sm.add_widget(screen)
        self.screens.append(screen)
        for s in self.screens:
            s.log = self.logger

        self.logger("------------------------------------------------------------------")
        self.logger("<General>")
        t = time.time()
        d =datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
        self.logger('  date = "%s"' % d)
        self.logger('  timestamp = %s' % t)
        self.logger("")
        self.logger("<Timeline>")
        self.logger("")
        random.seed(123)
        return self.sm

kivy.require('1.9.0')
Window.size = (1920, 1080)
Window.fullscreen = True
Config.set('kivy', 'desktop', '1')
Config.set('kivy', 'loglevel', 'error')

Config.set('kivy', 'exit_on_escape', '1')


if len(sys.argv) != 2:
    print("Usage: PerceptionMD STUDY_DESCRIPTION_FILE")
    sys.exit(1)

if not os.path.exists(sys.argv[1]):
    print("Usage: PerceptionMD STUDY_DESCRIPTION_FILE")
    print("Note: the file must exist and readable!")
    sys.exit(1)

explang_mm = metamodel_from_file('perception.tx')
model = explang_mm.model_from_file(sys.argv[1])

defaultvalues = {"font_size": 32,'logfile':'results.txt',
"random_seed" : "time",
"input_label_font_size":32,
"input_field_font_size":32,
"title_font_size":64,
"background_color":"None",
"button_font_size":48,
"button_size":48,
"button_font_color":"None",
"button_background_color":"None"}

contents = dict()
settings = dict()
settings.update(defaultvalues)
for content in model.contents:
    k = content.name[1:-1]
    v = content.content
    contents[k] = v

for kv in model.settings.keyvalue:
    k,v=kv.key,kv.value
    if len(v)==1:
        settings[k]=v[0]
    elif len(v)==0:
        settings[k]=None
    else:
        settings[k]=v

Builder.load_file("widgets/infoscreen.kv")

os.chdir(os.path.dirname(sys.argv[1]))

if __name__ == '__main__':
    app = InfoApp()
    app.contents = contents
    app.settings = settings
    app.logger = Logger(settings['logfile'])
    app.events = model.timeline.events
    app.run()
