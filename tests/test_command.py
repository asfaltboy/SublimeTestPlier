from typing import List
from unittest import TestCase, mock
import sys

from .sublime_mock import sublime, known_commands
from ..python_test_plier import RunPythonTestsCommand
from .. import utils

exec_cmd = mock.Mock()
ansi_cmd = mock.Mock()

known_commands["run_python_tests"] = RunPythonTestsCommand
known_commands["ansi_color_build"] = ansi_cmd
known_commands["exec"] = exec_cmd

TEST_CONTENT = """import unittest
class TestCase(unittest.TestCase):
    def test_fail(self):
        assert False

    def test_success(self):
        assert True

"""
DEFAULT_CMD_ARGS = ["--doctest-modules", "--doctest-ignore-import-errors", "-v"]


class TestPlierCommand(TestCase):
    def setUp(self):
        self.selection = []  # type: ignore
        self.window = sublime.active_window()
        self.view = self.window.new_file()

        self.substrings: List[str] = []
        self.view.substr = mock.Mock(side_effect=self.substrings)
        self.view.sel = mock.Mock(return_value=self.selection)
        self.view.file_name = mock.Mock(return_value="file.py")
        self.setText(TEST_CONTENT)
        self.view.substr.return_value = self.mock_selection(0, 0)
        self.custom_kwargs = dict(
            cmd=["nosetests", "-k {filename}:{test_class}.{test_func}"], sep_cleanup=":"
        )
        self.debug_patcher = mock.patch.object(utils, "DEBUG", return_value=True)
        self.debug_patcher.start()
        self.addCleanup(self.debug_patcher.stop)

    def tearDown(self):
        exec_cmd.reset_mock()
        ansi_cmd.reset_mock()

    def setText(self, string):
        self.view.run_command("insert", {"characters": string})

    def mock_region(self, r, c):
        self.view.rowcol.return_value = (r, c)
        return mock.Mock(a=r + c)

    def mock_selection(self, r, c, substring=""):
        self.selection.append(self.mock_region(r, c))
        self.substrings = [TEST_CONTENT, substring]
        self.view.substr.side_effect = self.substrings

    @mock.patch("os.listdir", return_value=["SublimeANSI"])
    def test_command_with_ansi_installed(self, listdir):
        self.view.run_command("run_python_tests")
        assert exec_cmd.called is False
        ansi_cmd.assert_called_once_with(
            dict(
                working_dir="",
                env={},
                syntax="Packages/ANSIescape/ANSI.tmLanguage",
                cmd=[
                    "pytest",
                ]
                + DEFAULT_CMD_ARGS
                + [
                    "file.py",
                ],
            )
        )

    def test_command_executed_with_filename(self):
        self.view.run_command("run_python_tests")
        exec_cmd.assert_called_once_with(
            dict(
                working_dir="",
                env={},
                cmd=[
                    "pytest",
                ]
                + DEFAULT_CMD_ARGS
                + [
                    "file.py",
                ],
            )
        )

    def test_command_executed_without_filename(self):
        self.view.file_name.return_value = ""
        self.view.run_command("run_python_tests")
        exec_cmd.assert_called_once_with(
            dict(
                working_dir="",
                env={},
                cmd=[
                    "pytest",
                ]
                + DEFAULT_CMD_ARGS
                + [],
            )
        )

    def test_command_executed_with_selection(self):
        self.view.substr.return_value = self.mock_selection(0, 0, "test 1")
        self.view.run_command("run_python_tests")
        exec_cmd.assert_called_once_with(
            dict(
                working_dir="",
                env={},
                cmd=[
                    "pytest",
                    "-k test 1",
                ]
                + DEFAULT_CMD_ARGS
                + [
                    "file.py",
                ],
            )
        )

    def test_command_executed_with_cursor_on_class(self):
        self.view.substr.return_value = self.mock_selection(1, 0)
        self.view.run_command("run_python_tests")
        exec_cmd.assert_called_once_with(
            dict(
                working_dir="",
                env={},
                cmd=[
                    "pytest",
                ]
                + DEFAULT_CMD_ARGS
                + [
                    "file.py::TestCase",
                ],
            )
        )

    def test_custom_cmd_with_cursor(self):
        self.view.substr.return_value = self.mock_selection(2, 2)
        self.view.run_command("run_python_tests", **self.custom_kwargs)
        exec_cmd.assert_called_once_with(
            dict(
                working_dir="",
                env={},
                cmd=[
                    "nosetests",
                    "-k file.py:TestCase.test_fail",
                ],
            )
        )

    def test_custom_cmd_without_file(self):
        self.view.file_name.return_value = ""
        self.view.run_command("run_python_tests", **self.custom_kwargs)
        exec_cmd.assert_called_once_with(
            dict(working_dir="", env={}, cmd=["nosetests", "-k "])
        )

    def test_custom_unittest_module_relative_to_project(self):
        self.view.file_name = mock.Mock(return_value="/SublimeTestPlier/tests/file.py")
        self.view.substr.return_value = self.mock_selection(2, 2)
        custom_kwargs = self.custom_kwargs.copy()
        custom_kwargs["cmd"] = ["unittest", "{module}.{test_class}.{test_func}"]

        # default: module relative to root of project
        self.window.extract_variables.return_value = {
            "project_path": "/",
            "project_base_name": "SublimeTestPlier",
        }
        self.view.run_command("run_python_tests", **custom_kwargs)
        exec_cmd.assert_called_once_with(
            dict(
                working_dir="",
                env={},
                cmd=[
                    "unittest",
                    "tests.file.TestCase.test_fail",
                ],
            )
        )

    def test_custom_unittest_module_relative_to_working_dir(self):
        self.view.file_name = mock.Mock(return_value="/SublimeTestPlier/tests/file.py")
        self.view.substr.return_value = self.mock_selection(2, 2)
        custom_kwargs = self.custom_kwargs.copy()
        custom_kwargs["cmd"] = ["unittest", "{module}.{test_class}.{test_func}"]

        # default: module relative to root of project
        self.window.extract_variables.return_value = {
            "project_path": "/",
            "project_base_name": "SublimeTestPlier",
        }

        # custom: module relative to the specified working dir in build system
        custom_kwargs["working_dir"] = "/SublimeTestPlier/tests/"
        self.view.run_command("run_python_tests", **custom_kwargs)
        exec_cmd.assert_called_once_with(
            dict(
                working_dir="/SublimeTestPlier/tests/",
                env={},
                cmd=[
                    "unittest",
                    "file.TestCase.test_fail",
                ],
            )
        )

    def test_command_external_python_ast(self):
        import tempfile

        # create a temporary file and write some data to it
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as fp:
            fp.write(TEST_CONTENT.encode())
            fp.close()

            self.view.file_name.return_value = fp.name
            self.view.substr.return_value = self.mock_selection(1, 0)
            python = sys.executable
            self.view.run_command("run_python_tests", python_executable=python)

        exec_cmd.assert_called_once_with(
            dict(
                working_dir=mock.ANY,
                env=mock.ANY,
                cmd=[
                    "pytest",
                ]
                + DEFAULT_CMD_ARGS
                + [
                    "%s::TestCase" % fp.name,
                ],
            )
        )
