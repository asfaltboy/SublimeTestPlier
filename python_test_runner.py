# -*- coding: utf-8 -*-

import sublime
import sublime_plugin

DEBUG = False
DEFAULT_CMD = {'cmd': ["py.test", "-k {selection}"]}


class PythonTestRunnerCommand(sublime_plugin.WindowCommand):
    def run(self, *args, **kwargs):
        self.window.run_command("run_python_tests", kwargs)


class RunPythonTestsCommand(sublime_plugin.WindowCommand):
    def setup_runner(self):
        settings = sublime.load_settings("python_test_runner.sublime-settings")
        print("Settings: %s" % vars(settings))
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
                print("Selection: {} ({})".format(selected_string, selection))
                return selected_string

    def run(self, *args, **command_kwargs):
        print("Args: %s" % list(args))
        print("Kwargs: %s" % command_kwargs)
        self.setup_runner()

        kwargs = DEFAULT_CMD
        kwargs['cmd'].append(self.filename)
        kwargs.update(command_kwargs)

        selection = self.get_selection() or ''
        kwargs['cmd'] = [p.format(selection=selection).strip(":")
                         for p in kwargs['cmd']]

        # return super().run(*args, **kwargs)
        return self.window.run_command("ansi_color_build", kwargs)
        # return self.window.run_command("exec", kwargs)
