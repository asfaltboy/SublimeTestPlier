"""
Utilities for parsing text position in python code, through AST,
and returning a test class/method name.
"""
from __future__ import print_function
import os
import subprocess

import sublime
from debug_tools import getLogger

from .. import test_parser

log = getLogger( 1, __name__ )


def DEBUG(value=None):
    settings = sublime.load_settings("TestPlier.sublime-settings")
    if value is None:
        return settings.get('debug', False)

    settings['debug'] = value
    settings = sublime.save_settings("TestPlier.sublime-settings")


def get_first_selection(view):
    view.settings().set('__vi_external_disable', True)
    selection = list(view.sel())
    view.settings().set('__vi_external_disable', False)
    if not selection:
        # cursor not in view
        return None

    log(2, "Selection: %s" % selection)

    # get first selection region
    return selection[0]


def get_selection_content(view):
    # return selected region as string if non-empty
    r = get_first_selection(view)
    selected_string = view.substr(r)
    log(2, "selected string: ", selected_string)
    if selected_string.strip():
        log(2, "Selection: %s (%s)" % (selected_string, r))
        return selected_string


def get_test_external_python(python, filename, line):
    args = [python, os.path.abspath(test_parser.__file__), filename, str(line)]
    output = subprocess.check_output(args)
    return tuple((part.decode('utf8') for part in output.strip().split(b',')))


def get_test(view, use_python=None):
    """
    This helper method which locates a cursor/region in given view
    and returns selected/containing test class/method.
    """
    r = get_first_selection(view)
    if r is None:
        log(2, "No selection found: ", r)
        return

    # try to detect if r is inside class/method
    source = view.substr(sublime.Region(0, view.size()))
    # log(2, "source is: ", source)
    line, col = view.rowcol(int(r.a))
    line = line + 1
    assert line, ('No line found in region: %s' % r)
    log(2, 'Position in code -> line %s, use_python: %s' % (line, use_python))

    if use_python:
        filename = view.file_name()
        assert filename, 'Cannot use_python without a filename'
        class_name, method_name = get_test_external_python(use_python, filename, line)
    else:
        parser = test_parser.TestParser(source, debug=DEBUG(), ignore_bases=['object'])
        class_name, method_name = parser.parse(line)
    log(2, 'Found class/name: %s/%s' % (class_name, method_name))
    return class_name, method_name


def get_default_command():
    ITERM_SCRIPT = b"""-- iTerm3 applescript launcher
set test_cmd to system attribute "TEST_CMD"

tell application "iTerm"
    activate
    if (count of windows) = 0 then
        set t to (create window with default profile)
    else
        set t to current window
    end if
    tell t
        tell current session
            write text test_cmd
        end tell
    end tell
end tell"""

    PYTHON_SCRIPT = b"""# Run simple applescript to launch iTerm2 with given command
import os
import shlex
import subprocess
import sys


def main():
    os.environ['TEST_CMD'] = os.environ.get('TEST_CMD', ' '.join(sys.argv[1:]))
    CUR_DIR = os.path.abspath(os.path.dirname(__file__))
    applescript = os.path.join(CUR_DIR, 'launch_in_iterm.applescript')
    cmd = 'osascript "%s"' % applescript
    print(cmd)
    full_cmd = shlex.split(cmd)
    print(full_cmd)
    subprocess.Popen(full_cmd).wait()


if __name__ == '__main__':
    main()

"""
    ITERM_SCRIPT_FILENAME = "launch_in_iterm.applescript"
    PYTHON_SCRIPT_FILENAME = "run_externally.py"
    packages = sublime.packages_path()
    script_dir = os.path.join(packages, "User", "Test Plier", "utils", )

    # copy the external scripts to user dir to expose to system
    if not os.path.exists(script_dir):
        os.makedirs(script_dir)

    iterm_script_full_path = os.path.join(script_dir, ITERM_SCRIPT_FILENAME)
    if not os.path.exists(iterm_script_full_path):
        with open(iterm_script_full_path, "wb") as out_f:
            out_f.write(ITERM_SCRIPT)

    python_script_full_path = os.path.join(script_dir, PYTHON_SCRIPT_FILENAME)
    if not os.path.exists(python_script_full_path):
        with open(python_script_full_path, "wb") as out_f:
            out_f.write(PYTHON_SCRIPT)

    return ["python", python_script_full_path]
