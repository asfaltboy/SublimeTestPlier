from __future__ import print_function
import ast


class TestParser(ast.NodeVisitor):
    """
    Extract class/test which contains given line number.

    Note: does not detect if line is just below class
          but before another root entity begins.


    >>> s = '''from mymodule.tests import TestClass
    ...
    ...
    ... class AnotherClass(object):
    ...     def test_method(self):
    ...         assert True
    ...
    ...
    ... # test something
    ...
    ... class SomeTest(TestClass):
    ...     class_property = True
    ...
    ...     def test_addition(self):
    ...         def helper(a):
    ...             return a + 1
    ...
    ...         return self.assertEqual(helper(2), 3)
    ...
    ...
    ... def func_test():
    ...     assert 1
    ... '''

    >>> parser = TestParser(source=s)
    >>> parser.parse(line=2)
    (None, None)
    >>> parser.parse(line=4)
    ('AnotherClass', None)
    >>> parser.parse(line=5)
    ('AnotherClass', 'test_method')
    >>> parser.parse(line=7)
    ('AnotherClass', 'test_method')
    >>> parser.parse(line=11)
    ('SomeTest', None)
    >>> parser.parse(line=12)
    ('SomeTest', None)
    >>> parser.parse(line=13)
    ('SomeTest', None)
    >>> parser.parse(line=14)
    ('SomeTest', 'test_addition')
    >>> parser.parse(line=15)
    ('SomeTest', 'test_addition')
    >>> parser.parse(line=16)
    ('SomeTest', 'test_addition')
    >>> parser.parse(line=17)
    ('SomeTest', 'test_addition')
    >>> parser.parse(line=18)
    ('SomeTest', 'test_addition')
    >>> parser.parse(line=21)
    (None, 'func_test')
    >>> parser.parse(line=22)
    (None, 'func_test')

    """

    def __init__(self, source, debug=False):
        self.nearest_class = None
        self.nearest_func = None
        self.source = source
        self.debug = debug
        self._log("Parsing source: ", self.source[:10],
                  '...', self.source[-10:])

    def _log(self, *args):
        if not self.debug:
            return
        print(*args)

    def parse(self, line):
        self.lineno = line
        tree = ast.parse(self.source)
        self.visit(tree)
        return (
            getattr(self.nearest_class, 'name', None),
            getattr(self.nearest_func, 'name', None),
        )

    def should_stop(self, node):
        assert self.lineno, 'line number required'
        if node.lineno > self.lineno:
            self._log("Stop parsing node lineno %s / our lineno %s" % (
                node.lineno, self.lineno))
            return True

    def inside_class(self, node):
        return (
            self.nearest_class and
            node.col_offset > self.nearest_class.col_offset
        )

    def first_argument_is_self(self, node):
        if not node.args.args:
            self._log("No arguments: ", vars(node.args))
            return False
        first_arg = node.args.args[0]
        self._log("First argument is ", first_arg)
        arg_name = getattr(first_arg, 'arg', getattr(first_arg, 'id', None))
        self._log("Argument Name: ", arg_name)
        return arg_name == 'self'

    def is_method(self, node):
        if not self.inside_class(node):
            self._log("Not inside class: ", vars(node))
            return False
        return self.first_argument_is_self(node)

    def visit_ClassDef(self, node):
        self._log('line: ', (node.lineno))
        if self.should_stop(node):
            return
        elif self.inside_class(node):
            self._log("Skip inside nested class: ", vars(node))
            # ignore nested classes
            return self.generic_visit(node)

        self.nearest_class = node   # set new class node
        self.nearest_func = None  # reset method node
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self._log('line: ', (node.lineno))
        if self.should_stop(node):
            return
        elif self.is_method(node):
            self._log("Method found: ", vars(node))
            self.nearest_func = node  # set method
        elif not self.inside_class(node):
            self._log("Function found: ", vars(node))
            self.nearest_class = None
            self.nearest_func = node
        return self.generic_visit(node)
