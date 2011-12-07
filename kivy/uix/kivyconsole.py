# -*- coding: utf-8 -*-
'''
KivyConsole
======

.. image:: images/kivyConsole.jpg
    :align: right

:class:`KivyConsole` is a :class:`~kivy.uix.widget.Widget`
Purpose: Providing a system console for debugging kivy by running another
instance of kivy in this console and displaying it's output.
To configure, you can use

cached_history :
cached_commands :
font :
font_size:

''Versionadded:: 1.0.?TODO

''Usage:

    parent.add_widget(KivyConsole())

TODO: Ensure unicode handling

Inside the console you can use the following shortcuts:
Shortcut                     Function
_________________________________________________________
PGup           Search for previous command inside command history
               starting with the text before current cursor position

PGdn           Search for Next command inside command history
               starting with the text before current cursor position

UpArrow        Replace command_line with previous command

DnArrow        Replace command_line with next command
               (only works if one is not at last command)

Tab            If there is nothing before the cursur when tab is pressed
                   contents of current directory will be displayed.
               '.' before cursur will be converted to './'
               '..' to '../'
               If there is a path before cursur position
                   contents of the path will be displayed.
               else contents of the path before cursor containing
                    the commands matching the text before cursur will
                    be displayed
'''

__all__ = ('KivyConsole', )

import shlex, subprocess, thread, os

from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.image import Image
from kivy.uix.button import Button
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

    '''
    cached_history = NumericProperty(200)
    '''Indicates the No. of lines to cache. Defaults to 200

    :data:`cached_history` is an :class:`~kivy.properties.NumericProperty`,
    Default to '200'
    '''

    cached_commands = NumericProperty(90)
    '''Indicates the no of commands to cache. Defaults to 90

    :data:`cached_commands` is a :class:`~kivy.properties.NumericProperty`,
    Default to '90'
    '''
    font = StringProperty('fonts/DroidSansMono.ttf')
    '''Indicates the font Style used in the console
    :data:`font` is a :class:`~kivy.properties.StringProperty`,
    Default to 'droid'
    '''

    font_size = NumericProperty(9)
    '''Indicates the size of the font used for the console
    :data:`font_size` is a :class:`~kivy.properties.NumericProperty`,
    Default to '9'
    '''

    textcache = StringProperty('')
    '''Indicates the textcache of the commands and their output
    :data:`textcache` is a :class:`~kivy.properties.StringProperty`,
    Default to ''
    '''

    def __init__(self, **kwargs):
        super(KivyConsole, self).__init__(**kwargs)
        #initialisations
        self.txtinput_command_line_refocus = False
        self.win                  = None
        self.scheduled            = False
        self.command_history      = []
        self.command_history_pos  = 0
        self.cur_dir              = os.getcwdu()
        self.txtinput_history_box = TextInput(
                                        size_hint = (1,.89),
                                        font      = self.font,
                                        font_size = self.font_size,
                                        text      = self.textcache)
        self.txtinput_command_line= TextInput(
                                        multiline = False,
                                        size_hint = (1,None),
                                        font      = self.font,
                                        font_size = self.font_size,
                                        text      = '['+ self.cur_dir +']:',
                                        height    = 27)
        self.txtinput_run_command_refocus         = False

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
            l_curdir= len(self.cur_dir)+3
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
                    self.txtinput_command_line.text = ''.join(('[',
                                                               self.cur_dir,
                                                               ']:',
                                                               cmd))
                    move_cursor_to(col)
                    return
            self.command_history_pos = max_len + 1

        if self.txtinput_command_line.focus:
            if l[1] ==273:
                #up arrow: display previous command
                if self.command_history_pos> 0 :
                    self.command_history_pos = self.command_history_pos - 1
                    self.txtinput_command_line.text = ''.join(
                                                      ('[',self.cur_dir,']:',
                              self.command_history[self.command_history_pos]))
                return
            if l[1] == 274:
                #dn arrow: display next command
                if self.command_history_pos < len(self.command_history) - 1:
                    self.command_history_pos = self.command_history_pos + 1
                    self.txtinput_command_line.text = ''.join(
                                                     ('[', self.cur_dir, ']:',
                              self.command_history[self.command_history_pos]))
                else:
                    self.command_history_pos = len(self.command_history)
                    self.txtinput_command_line.text = ''.join(('[',
                                                               self.cur_dir,
                                                               ']:'))
                col = len(self.txtinput_command_line.text)
                move_cursor_to(col)
                return
            if l[1] == 9:
                #tab: autocomplete [==== ]% done
                def display_dir(cur_dir, starts_with = None):
                    starts_with_is_not_None = starts_with is not None
                    if starts_with_is_not_None:
                        len_starts_with = len(starts_with)
                    
                    self.textcache = ''.join((self.textcache,
                                              'contents of directory: ',
                                              cur_dir,
                                              '\n'))
                    txt = ''
                    no_of_matches = 0
                    for _file in  os.listdir(cur_dir):
                         if starts_with_is_not_None:
                             if _file[:len_starts_with] == starts_with:
                                 txt = ''.join((txt, _file, ' '))
                                 no_of_matches += 1
                         else:
                             self.textcache = ''.join((self.textcache,_file,'\t'))
                    if no_of_matches == 1:
                        self.txtinput_command_line.text = ''.join(('[',
                                                          self.cur_dir,
                                                          ']:',
                                                          text_before_cursor,
                                                          txt[len_starts_with:],
                                      self.txtinput_command_line.text[col:]))
                    elif no_of_matches > 1:
                        self.textcache = ''.join((self.textcache, txt))
                    self.textcache = ''.join((self.textcache, '\n'))

                #send back space to command line -remove the tab
                self.txtinput_command_line.do_backspace()
                # store text before cursor for comparison
                l_curdir= len(self.cur_dir)+3
                col     = self.txtinput_command_line.cursor_col
                text_before_cursor = self.txtinput_command_line\
                                     .text[l_curdir: col]
                #if empty or space before: list cur dir
                if text_before_cursor == ''\
                   or self.txtinput_command_line.text[col-1] == ' ':
                    display_dir(self.cur_dir)
                #if in mid command:
                else:
                    # list commands in PATH var starting with text before cursor
                    # split command into path till the seperator
                    cmd_start  = text_before_cursor.rfind(' ')
                    cmd_start += 1
                    cmd_end = text_before_cursor.rfind(os.sep)
                    len_txt_bef_cur = len(text_before_cursor)-1
                    if cmd_end == len_txt_bef_cur:
                        #display files in path
                        display_dir(''.join((self.cur_dir, os.sep,
                                    text_before_cursor[cmd_start:cmd_end])))
                    elif text_before_cursor[len_txt_bef_cur] == '.':
                        #if / already there return
                        if len(self.txtinput_command_line.text) > col\
                           and self.txtinput_command_line.text[col] ==os.sep:
                            return
                        # insert at cursor os.sep: / or \
                        self.txtinput_command_line.text = ''.join(('[',
                                                          self.cur_dir,
                                                          ']:',
                                                          text_before_cursor,
                                                          os.sep,
                                      self.txtinput_command_line.text[col:]))
                    else:
                        if cmd_end < 0 :
                            cmd_end = cmd_start
                        else:
                            cmd_end += 1
                        display_dir(''.join((self.cur_dir,
                                             os.sep,
                                     text_before_cursor[cmd_start:cmd_end])),
                                   text_before_cursor[cmd_end:])
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
                #Home: cursor should not go to the left of cur_dir
                col = len(self.cur_dir)+3
                move_cursor_to(col)
                if len(l[4]) > 0 and l[4][0] == 'shift':
                    self.txtinput_command_line.selection_to = col
                return
            if l[1] == 276 or l[1] == 8:
                #left arrow/bkspc: cursor should not go left of cur_dir
                col = len(self.cur_dir)+3
                if self.txtinput_command_line.cursor_col < col:
                    if l[1] == 8:
                        self.txtinput_command_line.text = ''.join(
                                                          ('[',
                                                          self.cur_dir,
                                                          ']:'))
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
            if self.txtinput_run_command_refocus:
                self.txtinput_run_command_refocus = False
                instance.focus = True
                instance.scroll_x = 0
                instance.text = ''

    def on_enter(self, *l):

        def remove_command_interaction_widgets(*l):
            #command finished : remove widget responsible for interaction with it
            parent.remove_widget(self.interact_layout)
            self.interact_layout = None
            #enable running a new command
            parent.add_widget(self.txtinput_command_line)
            self.txtinput_command_line.focus = True

        def run_cmd(*l):
            # this is run inside a thread so take care avoid gui ops
            try:
                cmd = shlex.split(str(command))
            except ValueError, err:
                cmd = ''
                self.textcache      = ''.join((self.textcache,
                                                   str(err.strerror),
                                                   ' < ', command, ' >\n'))
            if len(cmd) >0:
                try:
                    #execute command
                    self.popen_obj  = subprocess.Popen(
                      cmd,
                      bufsize       = -1,
                      stdout        = subprocess.PIPE,
                      stdin         = subprocess.PIPE,
                      stderr        = subprocess.STDOUT,
                      preexec_fn    = None,
                      close_fds     = False,
                      shell         = False,
                      cwd           = self.cur_dir,
                      env           = None,
                      universal_newlines = False,
                      startupinfo   = None,
                      creationflags = 0)
                    txt                 = self.popen_obj.stdout.readline()
                    while txt != '':
                        self.popen_obj.stdout.flush()
                        txt             = txt.decode('utf-8')
                        self.textcache  = ''.join((self.textcache, txt))
                        txt             = self.popen_obj.stdout.readline()
                except OSError or ValueError, err:
                    self.textcache      = ''.join((self.textcache,
                                                   str(err.strerror),
                                                   ' < ', command, ' >\n'))

            self.popen_obj = None
            Clock.schedule_once(remove_command_interaction_widgets)

        #append text to textcache
        self.textcache = ''.join((self.textcache,
                                  self.txtinput_command_line.text,
                                  '\n'))
        command = self.txtinput_command_line.text[len(self.cur_dir)+3:]

        if command  == '':
            self.txtinput_command_line_refocus = True
            return

        #store command in command_history
        if self.command_history_pos > 0:
            self.command_history_pos = len(self.command_history) 
            if self.command_history[self.command_history_pos-1] != command:
                self.command_history.append(command)
        else:
            self.command_history.append(command)

        self.command_history_pos = len(self.command_history)

        #on reaching limit(cached_lines) pop first command
        if len(self.command_history) >= self.cached_commands:
            self.command_history = self.command_history[1:]

        # if command = cd change directory
        if command.startswith('cd '):
            try:
                os.chdir(self.cur_dir + os.sep + command[3:])
                self.cur_dir = os.getcwdu()
                self.txtinput_command_line.text = ''.join(('[', self.cur_dir, ']:'))
            except OSError, err:
                self.textcache = ''.join((self.textcache,
                                          err.strerror,
                                          '\n'))
            self.txtinput_command_line_refocus = True
            return

        self.txtinput_command_line.text = ''.join(('[', self.cur_dir, ']:'))
        #store output in textcache
        parent = self.txtinput_command_line.parent
        #disable running a new command while and old one is running
        parent.remove_widget(self.txtinput_command_line)
        #add widget for interaction with the running command
        txtinput_run_command = TextInput(multiline = False,
                                         font_size = self.font_size,
                                         font = self.font)

        def interact_with_command(*l):
            if not self.popen_obj:
                return
            txt = l[0].text + '\n'
            self.popen_obj.stdin.write(txt)
            self.popen_obj.stdin.flush()
            self.txtinput_run_command_refocus = True


        self.txtinput_run_command_refocus = False
        txtinput_run_command.bind(on_text_validate = interact_with_command)
        txtinput_run_command.bind(focus = self.on_focus)
        btn_kill = Button(text   ="kill",
                          width  = 27,
                       size_hint = (None, 1))

        def kill_process(*l):
            self.popen_obj.kill()

        self.interact_layout = GridLayout(rows = 1,
                                          cols = 2,
                                        height = 27,
                                     size_hint = (1, None))
        btn_kill.bind(on_press = kill_process)
        self.interact_layout.add_widget(txtinput_run_command)
        self.interact_layout.add_widget(btn_kill)
        parent.add_widget(self.interact_layout)

        txtinput_run_command.focus = True
        thread.start_new_thread(run_cmd,())


    def on_text(self, instance, txt):
        if instance is self.txtinput_history_box:
            #check if history_box has more text than indicated buy
            #self.cached_history and remove excess lines from top if so
            split_lines = self.textcache.splitlines(True)
            _lines = len(split_lines)
            extra_lines = _lines  - self.cached_history
            if extra_lines > 0:
                removelen = 0
                for line in split_lines[:extra_lines]:
                    removelen += len(line)
                self.textcache = self.textcache[removelen:]

            #disable editing while still allowing for
            #cut copy/paste operations
            self.txtinput_history_box.text = self.textcache
        else:
            #instance is command_line
            pass

