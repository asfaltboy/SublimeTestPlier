# -*- coding: utf-8 -*-
import os
import re

import sublime
import sublime_plugin

from . import utils


class RunPythonTestsCommand(sublime_plugin.WindowCommand):
    external_runner = None

    def __init__(self, window=None):

        if window:
            super().__init__(window)

        else:
            super().__init__()

        settings = sublime.load_settings("TestPlier.sublime-settings")
        self.run_last_valid_test = settings.get('run_last_valid_test', False)

        self.old_func_name = ''
        self.old_class_name = ''

    def ansi_installed(self):
        return 'sublimeansi' in list(map(str.lower, self.packages))

    def setup_runner(self):
        self.settings = sublime.load_settings("TestPlier.sublime-settings")
        utils._log("Settings: ", vars(self.settings))
        self.default_cmd = self.settings.get('default_cmd')
        utils._log("Default CMD: ", self.default_cmd)

        self.packages = os.listdir(self.window.extract_variables().get(
            'packages'))
        utils._log("Packages: ", self.packages)

        # get current filename
        self.filename = self.window.active_view().file_name()
        utils._log("Filename: ", self.filename)

        self.module = self._get_module(self.filename, base=None)
        utils._log("Module: ", self.module)

    def _get_module(self, filename, base):
        """ Convert a filename to a "module" relative to the working path """
        if not filename or not filename.endswith('.py'):
            utils._log('Cannot get module for non python-source file: ', filename)
            return ''  # only pytnon modules are supported
        base = base or os.path.join(
            self.window.extract_variables().get('project_path', ''),
            self.window.extract_variables().get('project_base_name', ''))
        utils._log('Getting module for file %s relative to base %s' % (filename, base))
        if not filename.startswith(base):
            utils._log('Cannot determine module path outside of directory')
            return ''
        return filename.replace(base, '').replace(os.path.sep, '.')[:-3].strip('.')

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
                cleaned_part = re.sub('%s+' % sep, sep, part).strip(sep)
                if cleaned_part:
                    result.append(cleaned_part)
            except KeyError:
                # ignore commands with unparsed parts
                continue
        return result

    def get_pattern(self, view):
        utils._log("View: ", view)
        pattern = view and utils.get_test(view)
        utils._log('Test pattern: ', pattern)
        if not pattern:
            self.class_name = self.func_name = None
            return
        self.class_name, self.func_name = pattern

        if self.run_last_valid_test:

            if self.func_name and not self.func_name.startswith( 'test_' ):
                self.func_name = self.old_func_name
                self.class_name = self.old_class_name

            self.old_func_name = self.func_name
            self.old_class_name = self.class_name

    def run(self, *args, **command_kwargs):
        utils._log('TestPlier running in debug mode')
        utils._log("Args: %s" % list(args))
        utils._log("Kwargs: %s" % command_kwargs)
        self.setup_runner()

        kwargs = self._get_default_kwargs()
        extra_args = command_kwargs.pop('extra_cmd_args', [])
        kwargs.update(command_kwargs)
        kwargs['cmd'].extend(extra_args)

        # TODO: infer from settings.python_interpreter and settings.src_root settings
        #       as used in https://github.com/JulianEberius/SublimePythonIDE
        if 'env' not in kwargs:
            kwargs['env'] = {}
        if 'working_dir' in kwargs:
            self.module = self._get_module(self.filename, base=kwargs['working_dir'])
            utils._log("Module updated: ", self.module)
        else:
            kwargs['working_dir'] = ''

        view = self.window.active_view()
        self.get_pattern(view)
        fmt_args = dict(
            module=self.module or '',
            filename=self.filename or '',
            test_class=self.class_name or '',
            test_func=self.func_name or '',
        )
        selection = utils.get_selection_content(view)
        if selection:
            fmt_args['selection'] = selection

        kwargs['cmd'] = self._format_placeholder(
            kwargs['cmd'], kwargs.pop('sep_cleanup'), **fmt_args)

        utils._log("Built command: ", kwargs)

        external = kwargs.get('external') or self.external_runner
        if external:
            utils._log('Running external command (%s)' % external)

            if isinstance(external, bool):
                # if "external": true, use our default
                default = utils.get_default_command()
                base_command = self.settings.get("default_external", default)
            elif isinstance(external, (list, tuple)):
                base_command = external
            else:
                raise Exception("External command must be either true/false"
                                " or a list of arguments")

            _env = ' '.join('%s=%s' % (ename, evalue) for
                            ename, evalue in kwargs['env'].items())
            change_dir_cmd = ''
            if kwargs['working_dir']:
                change_dir_cmd = 'cd {path} && '.format(path=kwargs['working_dir'])
            elif self.filename:
                # for running individual arbitrary test modules
                filename_dir = os.path.dirname(self.filename)
                change_dir_cmd = 'cd {path} && '.format(path=filename_dir)

            _cmd = '{cwd}{env_setup} {cmd}'.format(
                cwd=change_dir_cmd,
                cmd=' '.join(kwargs['cmd']),
                env_setup=_env,
            )
            cmd = (base_command) + [_cmd]
            kwargs['cmd'] = cmd
            utils._log('Running external runner with cmd: %s' % kwargs)
            return self.window.run_command("exec", {'cmd': cmd})
        elif self.ansi_installed():
            utils._log('Running internal command (with ANSI colors)')
            return self.window.run_command("ansi_color_build", kwargs)
        else:
            utils._log('Running internal command (without ANSI colors)')
            return self.window.run_command("exec", kwargs)
