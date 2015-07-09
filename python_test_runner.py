# -*- coding: utf-8 -*-
from __future__ import print_function
import os

import sublime
import sublime_plugin

DEBUG = False
DEFAULT_CMD = ["py.test", "-k {selection}"]


def _log(*args):
    if not DEBUG:
        return
    print(*args)


class PythonTestRunnerCommand(sublime_plugin.WindowCommand):
    def run(self, *args, **kwargs):
        self.window.run_command("run_python_tests", kwargs)


class RunPythonTestsCommand(sublime_plugin.WindowCommand):
    def ansi_installed(self):
        return 'sublimeansi' in list(map(str.lower, self.packages))

    def setup_runner(self):
        settings = sublime.load_settings("python_test_runner.sublime-settings")
        _log("Settings: %s" % vars(settings))
        self.packages = os.listdir(self.window.extract_variables().get(
            'packages'))

        _log("Packages: %s" % self.packages)
        # get current filename
        self.filename = self.window.active_view().file_name()

    def get_selection(self):
        view = self.window.active_view()
        if view:
            view.settings().set('__vi_external_disable', True)
            selection = list(view.sel())
            view.settings().set('__vi_external_disable', False)
            if selection:
                selected_string = view.substr(view.sel()[0])
                _log("Selection: {} ({})".format(selected_string, selection))
                return selected_string

    def run(self, *args, **command_kwargs):
        _log("Args: %s" % list(args))
        _log("Kwargs: %s" % command_kwargs)
        self.setup_runner()

        kwargs = {}
        kwargs['cmd'] = DEFAULT_CMD + [self.filename]
        if self.ansi_installed:
            kwargs['syntax'] = "Packages/ANSIescape/ANSI.tmLanguage"
        kwargs.update(command_kwargs)

        selection = self.get_selection() or ''
        kwargs['cmd'] = [p.format(selection=selection).strip(":")
                         for p in kwargs['cmd']]

        # return super().run(*args, **kwargs)
        if self.ansi_installed:
            return self.window.run_command("ansi_color_build", kwargs)
        return self.window.run_command("exec", kwargs)
