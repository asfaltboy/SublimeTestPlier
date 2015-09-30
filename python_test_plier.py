# -*- coding: utf-8 -*-
import os
import re

import sublime
import sublime_plugin

from .utils import get_test, _log, get_selection_content

# TODO: needs tests


class PythonTestRunnerCommand(sublime_plugin.WindowCommand):
    def run(self, *args, **kwargs):
        self.window.run_command("run_python_tests", kwargs)


class RunPythonTestsCommand(sublime_plugin.WindowCommand):
    def ansi_installed(self):
        return 'sublimeansi' in list(map(str.lower, self.packages))

    def setup_runner(self):
        self.settings = sublime.load_settings("test_plier.sublime-settings")
        _log("Settings: ", vars(self.settings))
        self.default_cmd = self.settings.get('default_cmd')
        _log("Default CMD: ", self.default_cmd)

        self.packages = os.listdir(self.window.extract_variables().get(
            'packages'))
        _log("Packages: ", self.packages)

        # get current filename
        self.filename = self.window.active_view().file_name()
        _log("Filename: ", self.filename)

    def _get_default_kwargs(self):
        kwargs = {
            'cmd': self.default_cmd,
            # trim the following string in-between interpolated parts
            'sep_cleanup': '::',
        }
        if self.ansi_installed():
            kwargs['syntax'] = "Packages/ANSIescape/ANSI.tmLanguage"
        return kwargs

    def _format_placeholder(self, cmd, sep, **kwargs):
        result = []
        for part in cmd:
            try:
                part = part.format(**kwargs).strip(sep).strip('.')
                cleaned_part = re.sub('%s+' % sep, sep, part)
                if cleaned_part:
                    result.append(cleaned_part)
            except KeyError:
                # ignore commands with unparsed parts
                continue
        return result

    def get_pattern(self, view):
        _log("View: ", view)
        pattern = view and get_test(view)
        _log('Test pattern: ', pattern)
        if not pattern:
            self.class_name = self.func_name = None
            return
        self.class_name, self.func_name = pattern

    def run(self, *args, **command_kwargs):
        _log("Args: %s" % list(args))
        _log("Kwargs: %s" % command_kwargs)
        self.setup_runner()

        kwargs = self._get_default_kwargs()
        kwargs.update(command_kwargs)

        view = self.window.active_view()
        self.get_pattern(view)
        fmt_args = dict(
            filename=self.filename or '',
            test_class=self.class_name or '',
            test_func=self.func_name or '',
        )
        selection = get_selection_content(view)
        if selection:
            fmt_args['selection'] = selection

        kwargs['cmd'] = self._format_placeholder(
            kwargs['cmd'], kwargs.pop('sep_cleanup'), **fmt_args)

        _log("Built command: ", kwargs)

        if self.ansi_installed():
            return self.window.run_command("ansi_color_build", kwargs)
        return self.window.run_command("exec", kwargs)
