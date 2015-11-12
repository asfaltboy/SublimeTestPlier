from unittest import TestCase, mock

from .sublime_mock import sublime, known_commands
from ..python_test_plier import RunPythonTestsCommand
from .. import utils

mock.patch.object(utils, 'DEBUG', True).start()

exec_cmd = mock.Mock()
ansi_cmd = mock.Mock()

known_commands['run_python_tests'] = RunPythonTestsCommand
known_commands['ansi_color_build'] = ansi_cmd
known_commands['exec'] = exec_cmd

TEST_CONTENT = """import unittest
class TestCase(unittest.TestCase):
    def test_fail(self):
        assert False

    def test_success(self):
        assert True

"""
DEFAULT_CMD_ARGS = ['--doctest-modules', '--doctest-ignore-import-errors', '-v']


class TestPlierCommand(TestCase):
    def setUp(self):
        self.selection = []
        self.window = sublime.active_window()
        self.view = self.window.new_file()

        self.substrings = []
        self.view.substr = mock.Mock(side_effect=self.substrings)
        self.view.sel = mock.Mock(return_value=self.selection)
        self.view.file_name = mock.Mock(return_value='file.py')
        self.setText(TEST_CONTENT)
        self.view.substr.return_value = self.mock_selection(0, 0)
        self.custom_kwargs = dict(
            cmd=["nosetests", "-k {filename}:{test_class}.{test_func}"],
            sep_cleanup=':'
        )

    def tearDown(self):
        exec_cmd.reset_mock()
        ansi_cmd.reset_mock()

    def setText(self, string):
        self.view.run_command("insert", {"characters": string})

    def mock_region(self, r, c):
        self.view.rowcol.return_value = (r, c)
        return mock.Mock(a=r+c)

    def mock_selection(self, r, c, substring=''):
        self.selection.append(self.mock_region(r, c))
        self.substrings = [TEST_CONTENT, substring]
        self.view.substr.side_effect = self.substrings

    @mock.patch('os.listdir', return_value=['SublimeANSI'])
    def test_command_with_ansi_installed(self, listdir):
        self.view.run_command("run_python_tests")
        assert exec_cmd.called is False
        ansi_cmd.assert_called_once_with(dict(
            syntax='Packages/ANSIescape/ANSI.tmLanguage',
            cmd=['py.test', 'file.py', ] + DEFAULT_CMD_ARGS))

    def test_command_executed_with_filename(self):
        self.view.run_command("run_python_tests")
        exec_cmd.assert_called_once_with(dict(
            cmd=['py.test', 'file.py', ] + DEFAULT_CMD_ARGS))

    def test_command_executed_without_filename(self):
        self.view.file_name.return_value = ''
        self.view.run_command("run_python_tests")
        exec_cmd.assert_called_once_with(dict(
            cmd=['py.test', ] + DEFAULT_CMD_ARGS))

    def test_command_executed_with_selection(self):
        self.view.substr.return_value = self.mock_selection(0, 0, 'test 1')
        self.view.run_command("run_python_tests")
        exec_cmd.assert_called_once_with(dict(
            cmd=['py.test', 'file.py', '-k test 1', ] + DEFAULT_CMD_ARGS))

    def test_command_executed_with_cursor_on_class(self):
        self.view.substr.return_value = self.mock_selection(1, 0)
        self.view.run_command("run_python_tests")
        exec_cmd.assert_called_once_with(dict(
            cmd=['py.test', 'file.py::TestCase', ] + DEFAULT_CMD_ARGS))

    def test_custom_cmd_with_cursor(self):
        self.view.substr.return_value = self.mock_selection(2, 2)
        self.view.run_command("run_python_tests", **self.custom_kwargs)
        exec_cmd.assert_called_once_with(dict(
            cmd=['nosetests', '-k file.py:TestCase.test_fail', ]))

    def test_custom_cmd_without_file(self):
        self.view.file_name.return_value = ''
        self.view.run_command("run_python_tests", **self.custom_kwargs)
        exec_cmd.assert_called_once_with(dict(
            cmd=['nosetests', '-k ']))
