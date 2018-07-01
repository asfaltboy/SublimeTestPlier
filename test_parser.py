"""
Find a test class and/or test method in given source code line.
See TestParser docstring below for details.

Usage:

    python test_parser.py <source_module> <line>

Example:

    > python test_parser.py your_source_file.py 4
    TestCase,test_method

"""
from __future__ import print_function
import ast
import sys


class TestParser(ast.NodeVisitor):
    """
    Given <source>, extract the top level class/function which contains given
    line number.

    Optional arguments:
    * <debug> output log statements
    * <ignore_bases> list of class base names to be skipped

    Note: currently if row is below last class/function and unindented it is
          still considered inside the last detected class/function.

    >>> from os import path
    >>> TEST_DIR = path.join(path.abspath(path.dirname(__file__)), 'tests')
    >>> module_source = open(path.join(TEST_DIR, '_fixture.py')).read()
    >>> parser = TestParser(source=module_source, ignore_bases=['object'])
    >>> parser.parse(line=4)
    (None, None)

    >>> list(set(map(parser.parse, (5, 7))))
    [(None, None)]

    >>> list(set(map(parser.parse, (36, 37, 38))))
    [(None, None)]

    >>> parser = TestParser(source=module_source)
    >>> parser.parse(line=1)
    (None, None)

    >>> parser.parse(line=4)
    ('AnotherClass', None)

    >>> list(set(map(parser.parse, (5, 7))))
    [('AnotherClass', 'test_method')]

    >>> list(set(map(parser.parse, (11, 12, 13))))
    [('SomeTest', None)]

    >>> list(set(map(parser.parse, (14, 15, 16, 17, 18))))
    [('SomeTest', 'test_addition')]

    >>> list(set(map(parser.parse, (21, 22))))
    [(None, 'func_test')]

    >>> list(set(map(parser.parse, (25, 26, 27, 28, 31))))
    [('ParentClass', None)]

    >>> list(set(map(parser.parse, (29, 30))))
    [('ParentClass', None)]

    >>> list(set(map(parser.parse, (32, 33))))
    [('ParentClass', 'parent_method')]

    # test decorated test case and decorated method
    >>> list(set(map(parser.parse, range(41, 44))))
    [('DecoratedTestClass', None)]

    >>> list(set(map(parser.parse, range(44, 47))))
    [('DecoratedTestClass', 'test_me')]

    # test first test is a func test
    >>> parser = TestParser(source=module_source)
    >>> parser.parse(line=2)
    (None, 'test_first')
    """
    nested_class = None

    def __init__(self, source, debug=False, ignore_bases=None):
        self.source = source
        self.ignore_bases = ignore_bases or []
        self.debug = debug
        self._log("Parsing source: ", self.source[:10],
                  '...', self.source[-10:])

    def _log(self, *args):
        if not self.debug:
            return
        print(*args)

    def parse(self, line):
        self.nearest_class = None
        self.nearest_func = None
        self.nearest_ignored = None
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

    def ignore_class(self, node):
        if not hasattr(node, 'bases'):
            self._log("Class %s has no bases (not a class?)" % node)
            return False
        self._log("Ignore if bases %s are in %s" %
                  (node.bases, self.ignore_bases))

        def should_ignore(base):
            if hasattr(base, 'id'):
                return base.id in self.ignore_bases
            elif hasattr(base, 'attr'):
                return base.attr in self.ignore_bases
            raise Exception('Unknown base node %s' % base)
        return any(map(should_ignore, node.bases))

    def inside_class(self, node):
        """
        Test whether node is inside a class definition.
        Test ignores classes whose base is in self.ignore_bases.
        """
        self._log("Testing if node %s is inside a class" % node)
        return (
            # verify none of the bases are in ignored bases
            not self.ignore_class(node) and
            # check if currently already inside a class
            self.nearest_class and
            # compare col offset to check if we unindented
            node.col_offset > self.nearest_class.col_offset and
            # also make sure we're not currently in an ignored class
            not self.nearest_ignored
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
        if self.nested_class and node.col_offset > self.nested_class.col_offset:
            self._log("Method is inside a nested class definition, skipping")
            return False
        return self.first_argument_is_self(node)

    def visit_ClassDef(self, node):
        self._log('line: ', (node.lineno))
        if self.should_stop(node):
            return
        elif self.inside_class(node):
            self._log("Skip inside nested class: ", vars(node))
            self.nested_class = node
            # ignore nested classes
            return self.generic_visit(node)

        self.nested_class = None

        if self.ignore_class(node):
            self.nearest_ignored = node
            self.nearest_class = None
        else:
            self.nearest_class = node   # set new class node
            self.nearest_ignored = None
        self.nearest_func = None  # reset method node
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self._log('line: ', (node.lineno))
        if self.should_stop(node):
            return
        elif self.is_method(node):
            self._log("Method found: ", vars(node))
            self.nearest_func = node  # set method
            self.nearest_ignored = None
        elif not self.inside_class(node) and not self.nearest_ignored:
            self._log("Function found: ", vars(node))
            self.nearest_class = None
            self.nearest_func = node
        return self.generic_visit(node)


def cli():
    if not len(sys.argv) == 3:
        sys.exit('Missing required arguments!\n%s' % __doc__)

    _, module, line = sys.argv

    with open(module) as module_file:
        source_code = module_file.read()
        parser = TestParser(source_code)
        result = parser.parse(line=int(line))
        printable_result = ','.join(part or '' for part in result)
        print(printable_result)


if __name__ == '__main__':
    cli()
