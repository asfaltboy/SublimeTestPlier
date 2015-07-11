"""
Utilities for parsing text position in python code, through AST,
and returning a test class/method name.
"""
from __future__ import print_function

import sublime
from .test_parser import TestParser

DEBUG = False


def _log(*args):
    """
    >>> DEBUG = False
    >>> _log("Test")

    >>> DEBUG = True
    >>> _log("Test")
    Test
    """
    if not DEBUG:
        return
    print(*args)


def get_first_selection(view):
    view.settings().set('__vi_external_disable', True)
    selection = list(view.sel())
    view.settings().set('__vi_external_disable', False)
    if not selection:
        # cursor not in view
        return None

    _log("Selection: %s" % selection)

    # get first selection region
    return selection[0]


def get_selection_content(view):
    # return selected region as string if non-empty
    r = get_first_selection(view)
    selected_string = view.substr(r)
    if selected_string.strip():
        _log("Selection: %s (%s)" % (selected_string, r))
        return selected_string


def get_test(view):
    """
    This helper method which locates a cursor/region in given view
    and returns selected/containing test class/method.
    """
    r = get_first_selection(view)

    # try to detect if r is inside class/method
    source = view.substr(sublime.Region(0, view.size()))
    line, col = view.rowcol(int(r.a))
    line = line + 1
    assert line, ('No line found in region: %s' % r)
    _log('Position in code -> line %s' % line)

    class_name, method_name = TestParser(source, debug=DEBUG).parse(line)
    _log('Found class/name: %s/%s' % (class_name, method_name))
    return class_name, method_name
