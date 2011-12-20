'''
A console implimentation using kivy
===================================

Test of the widget KivyConsole
'''
import subprocess

from kivy.app import App
from kivy.uix.kivyconsole import KivyConsole
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

class TestConsoleApp(App):

    def build(self):
        console = KivyConsole()
        lbl = Label(font_size = 9, halign = 'left', valign = 'bottom')
        bl = BoxLayout()
        bl.add_widget(lbl)
        bl.add_widget(console)
        #to run command
        console.stdin.write('uname -r')
        #or
        subprocess.Popen(('echo','ls -ls'), stdout = console.stdin)
        #to display something on stdout write to stdout
        console.stdout.write('this will be written to the stdout\n')
        # or
        p1 = subprocess.Popen('whoami', stdout = console.stdout, shell = True)
        #read from stdout
        #process is run in a diff thread give it time to complete
        #otherwise you might get a empty or partial string
        def read_output(*l):
            text = console.stdout.read()# or read (no_of_bytes) or readline()
            #return console
            lbl.text = text
            Clock.unschedule(read_output)

        from kivy.clock import Clock
        Clock.schedule_interval(read_output, .1)
        return bl



if __name__ in ('__main__', '__android__'):
    TestConsoleApp().run()