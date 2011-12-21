'''
A console implimentation using kivy
===================================

Test of the widget KivyConsole
'''
import subprocess

from kivy.app import App
from kivy.uix.kivyconsole import KivyConsole
from kivy.uix.label import Label

class TestConsoleApp(App):

    def build(self):
        console = KivyConsole()
        #console.stdin.write('ls -l')
        subprocess.Popen(('ls','-l'), stdout = console.stdout)
        #text = console.stdout.read()
        #subprocess.Popen('dir', stdout = console.stdout, shell = True)
        #text += console.stdout.read()
        #subprocess.Popen('ps aux', stdout = console.stdout, shell = True)
        #text += console.stdout.read()
        return console
        #return Label(text = text)


if __name__ in ('__main__', '__android__'):
    TestConsoleApp().run()