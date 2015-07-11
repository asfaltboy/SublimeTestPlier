from __future__ import print_function
import ast


class TestParser(ast.NodeVisitor):
    """
    Extract class/test which contains given line number.

    Note: does not detect global location if line is below class/function


    >>> parser = TestParser(source=open('test_fixture.py').read())
    >>> parser.parse(line=2)
    (None, None)

    >>> parser.parse(line=4)
    ('AnotherClass', None)

    >>> set(map(parser.parse, (5, 7)))
    set([('AnotherClass', 'test_method')])

    >>> set(map(parser.parse, (11, 12, 13)))
    set([('SomeTest', None)])

    >>> set(map(parser.parse, (14, 15, 16, 17, 18)))
    set([('SomeTest', 'test_addition')])

    >>> set(map(parser.parse, (21, 22)))
    set([(None, 'func_test')])

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
