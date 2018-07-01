import sys
import json
from os import path
from unittest import mock

_buffer = None


def insert_to_buffer(obj):
    global _buffer
    _buffer = (_buffer or '') + obj['characters']


packages = path.abspath(path.dirname(__file__))
known_commands = {
    'insert': insert_to_buffer,
}


def run_command(name, *args, **kwargs):
    assert name in known_commands, (
        '%s command not found. You need to import packages you need for your '
        'tests (or Mock them) and add them to `sublime_mock.known_commands`'
        ' dict') % name
    cmd = known_commands[name]
    if isinstance(cmd, type):
        print("Running command ", name, cmd.run)
        return cmd().run(*args, **kwargs)
    print("Running function ", name, cmd)
    return cmd(*args, **kwargs)


settings = None


def settings_loader(settings_file):
    """ Implicitly saves settings as a global fake dict """
    global settings
    if settings is None:
        settings = mock.MagicMock(spec_set=dict)
        assert settings_file == 'SublimeTestPlier.sublime-settings'
        settings_file_path = path.join(path.abspath(path.dirname(path.dirname(__file__))), settings_file)
        assert path.exists(settings_file_path), 'Invalid settings file %s' % settings_file_path
        with open(settings_file_path) as f:
            data = json.load(f)
            # settings.update(data)

        def getitem(name, default=None):
            return data.get(name, default)
        settings.__getitem__.side_effect = getitem
        settings.get.side_effect = getitem

        def setitem(name, val):
            data[name] = val
        settings.__setitem__.side_effect = setitem

    return settings


window_variables = {
    'packages': packages,
}
command_runner = mock.Mock(side_effect=run_command)
view = mock.Mock(run_command=command_runner, _buffer=_buffer)
window = mock.Mock(new_file=mock.Mock(return_value=view),
                   run_command=command_runner,
                   extract_variables=mock.Mock(return_value=window_variables),
                   active_view=mock.Mock(return_value=view))
sublime = mock.Mock(active_window=mock.Mock(return_value=window),
                    load_settings=mock.Mock(side_effect=settings_loader),
                    save_settings=mock.Mock(side_effect=settings_loader))

WindowCommand = type(object.__name__, (mock.MagicMock,),
                     dict(object.__dict__, window=window))
sublime_plugin = mock.MagicMock(WindowCommand=WindowCommand)

sys.modules['sublime'] = sublime
sys.modules['sublime_plugin'] = sublime_plugin
