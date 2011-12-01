# -*- coding: utf-8 -*-
'''
KivyConsole
======

.. image:: images/kivyConsole.jpg
    :align: right

:class:`KivyConsole` is a :class:`~kivy.uix.widget.Widget`
Purpose: Providing a system console for debugging kivy by running another
instance of kivy in this console and displaying it's output.
To configure, you can use  TODO: write config options

''Versionadded:: 1.0.?TODO

''Usage:

    parent.add_widget(Re_Size())
'''

__all__ = ('KivyConsole', )

import subprocess, thread

from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty, StringProperty
from kivy.factory import Factory
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.lang import Builder
from kivy.app import App

Builder.load_string('''
<KivyConsole>:
    cols:1
    rows:2
''')



class KivyConsole(GridLayout):
    '''This is a Console widget used for debugging and running external
    commands


    Events:

    '''
    cached_history = NumericProperty(200)
    '''Indicates the no of lines to cache defaults to 200

    :data:`cached_history` is an :class:`~kivy.properties.NumericProperty`,
    default to '200'
    '''

    cached_commands = NumericProperty(90)
    '''Indicates the no of commands to cache defaults to 90

    :data:`cached_commands` is an :class:`~kivy.properties.NumericProperty`,
    default to '90'
    '''
    textcache = StringProperty('')
    '''
    '''

    def __init__(self, **kwargs):
        super(KivyConsole, self).__init__(**kwargs)
        #initialisations
        self.txtinput_command_line_refocus = False
        pwd = subprocess.Popen('pwd', stdout=subprocess.PIPE).stdout.readline()
        pwd                       = pwd[:len(pwd)-1]
        self.win                  = None
        self.scheduled            = False
        self.command_history      = []
        self.command_history_pos  = 0
        self.cur_dir              = '['+ pwd +']:'
        self.txtinput_history_box = TextInput(\
                                        size_hint = (1,.89),\
                                        font_size = 9,\
                                        text      = self.textcache)
        self.txtinput_command_line= TextInput(\
                                        multiline = False,\
                                        size_hint = (1,None),\
                                        font_size = 9,\
                                        text      = self.cur_dir,\
                                        height    = 27)

        self.txtinput_command_line.bind(on_text_validate = self.on_enter)
        self.txtinput_command_line.bind(focus            = self.on_focus)
        self.txtinput_command_line.bind(text             = self.on_text)
        self.txtinput_history_box.bind(text              = self.on_text)

        self.add_widget(self.txtinput_history_box)
        self.add_widget(self.txtinput_command_line)

    def on_textcache(self, *l):
        #use schedule interval so as to fill TextInput Box
        #as few times as possible calling 'TextInput.text =' is sloooow
        def change_txtcache(*l):
            Clock.unschedule(change_txtcache)
            self.txtinput_history_box.text = self.textcache

        Clock.schedule_interval(change_txtcache, .5)

    def on_keyboard(self, *l):

        def move_cursor_to(col):
            self.txtinput_command_line.do_cursor_movement('cursor_home')
            c = 0
            while c < col:
                c+=1
                self.txtinput_command_line.do_cursor_movement('cursor_right')

        def search_history(up_dn):
            if up_dn == 'up':
                plus_minus = -1
            else:
                plus_minus = 1
            l_curdir= len(self.cur_dir)
            col     = self.txtinput_command_line.cursor_col
            command = self.txtinput_command_line.text[l_curdir: col]
            max_len = len(self.command_history) -1

            while max_len >= 0 :
                if plus_minus == 1:
                    if self.command_history_pos > max_len -1:
                        self.command_history_pos = max_len
                        return
                else:
                    if self.command_history_pos <= 0:
                        self.command_history_pos = max_len
                        return
                self.command_history_pos = self.command_history_pos + plus_minus
                cmd = self.command_history[self.command_history_pos]
                if  cmd[:len(command)] == command:
                    self.txtinput_command_line.text = self.cur_dir + cmd
                    move_cursor_to(col)
                    return
            self.command_history_pos = max_len + 1

        if self.txtinput_command_line.focus:
            if l[1] ==273:
                #up arrow: display previous command
                if self.command_history_pos> 0 :
                    self.command_history_pos = self.command_history_pos - 1
                    self.txtinput_command_line.text = self.cur_dir +\
                        self.command_history[self.command_history_pos]
                return
            if l[1] == 274:
                #dn arrow: display next command
                if self.command_history_pos < len(self.command_history) - 1:
                    self.command_history_pos = self.command_history_pos + 1
                    self.txtinput_command_line.text = self.cur_dir +\
                        self.command_history[self.command_history_pos]
                else:
                    self.command_history_pos = len(self.command_history)
                    self.txtinput_command_line.text = self.cur_dir
                col = len(self.txtinput_command_line.text)
                move_cursor_to(col)
                return
            if l[1] == 23:
                #tab: autocomplete TODO
                return
            if l[1] == 280:
                #pgup: search last command starting with...
                search_history('up')
                return
            if l[1] == 281:
                #pgdn: search next command starting with...
                search_history('dn')
                return
            if l[1] == 278:
                #Home: cursor should not go left of cur_dir
                col = len(self.cur_dir)
                move_cursor_to(col)
                if l[4][0] == 'shift':
                    self.txtinput_command_line.selection_to = col
                return
            if l[1] == 276 or l[1] == 8:
                #left arrow/bkspc: cursor should not go left of cur_dir
                if self.txtinput_command_line.cursor_col < len(self.cur_dir):
                    if l[1] == 8:
                        self.txtinput_command_line.text = self.cur_dir
                    col = len(self.cur_dir)
                    move_cursor_to(col)
                return

    def on_focus(self, instance, value):
        if value:
           #focused
           if instance is self.txtinput_command_line:
               if self.win is None:
                   win = self
                   while win.parent is not None and\
                       str(win)[:17] != '<kivy.core.window':
                       win = win.parent
                   self.win = win
                   win.bind(on_keyboard = self.on_keyboard)
        else:
            #defocused
            if self.txtinput_command_line_refocus:
                self.txtinput_command_line_refocus = False
                self.txtinput_command_line.focus = True
                self.txtinput_command_line.scroll_x = 0

    def on_enter(self, *l):

        def run_cmd(*l):
            try:
                #execute command
                self.popen_obj      = subprocess.Popen(str(command)\
                   .split(), stdout = subprocess.PIPE,\
                             stdin  = subprocess.PIPE,\
                             stderr = subprocess.STDOUT, shell = False)
                txt                 = self.popen_obj.stdout.readline()
                while txt != '':
                    txt             = txt.decode('utf-8')
                    self.textcache  = ''.join((self.textcache, txt))
                    txt             = self.popen_obj.stdout.readline()
            except OSError, err:
                self.textcache     += str(err.strerror) +' < '+command+' >\n'

            self.popen_obj = None
            #command finished : remove widget responsible for interaction with it
            parent.remove_widget(self.txtinput_run_command)
            self.txtinput_run_command = None
            #enable running a new command
            parent.add_widget(self.txtinput_command_line)
            self.txtinput_command_line.focus = True

        #append text to textcache
        self.textcache += self.txtinput_command_line.text + '\n'
        command = self.txtinput_command_line.text[len(self.cur_dir):]
        #store command in command_history
        if command  == '':
            self.txtinput_command_line_refocus = True
            return

        if self.command_history_pos > 0:
            if self.command_history[self.command_history_pos-1] != command:
                self.command_history.append(command)
        else:
            self.command_history.append(command)

        self.command_history_pos = len(self.command_history)
        if len(self.command_history) >= self.cached_commands:
            #on reaching limit(cached_lines) pop first command
            self.command_history = self.command_history[1:]

        #store output in textcache
        self.txtinput_command_line.text    = self.cur_dir
        parent = self.txtinput_command_line.parent
        #disable running a new command while and old one is running
        parent.remove_widget(self.txtinput_command_line)
        #add widget for interaction with the running command
        self.txtinput_run_command = TextInput(\
                                     multiline = False,\
                                     size_hint = (1,None),\
                                     font_size = 9,\
                                     height    = 27)

        def interact_with_command(*l):
            txt = l[0].text + '\n'
            self.popen_obj.stdin.write(txt)
            self.popen_obj.stdin.flush()

        self.txtinput_run_command.bind(on_text_validate = interact_with_command)
        parent.add_widget(self.txtinput_run_command)
        self.txtinput_run_command.focus = True
        thread.start_new_thread(run_cmd,())


    def on_text(self, instance, txt):
        if instance is self.txtinput_history_box:
            #check if history_box has more text than indicated buy
            #self.cached_history and remove excess lines from top if so
            split_lines = self.textcache.splitlines()
            while len(split_lines)  > self.cached_history:
                self.textcache = self.textcache[len(split_lines[0])+1:]
                split_lines = self.textcache.splitlines()


            #disable editing while still allowing for
            #cut copy/paste operations
            self.txtinput_history_box.text = self.textcache
        else:
            #instance is command_line
            pass

