'''
A console implimentation using kivy
===================================

Test of the widget KivyConsole
'''

from kivy.app import App
from kivy.uix.kivyconsole import KivyConsole

class TestConsoleApp(App):

    def build(self):
        return KivyConsole()


if __name__ in ('__main__', '__android__'):
    TestConsoleApp().run()