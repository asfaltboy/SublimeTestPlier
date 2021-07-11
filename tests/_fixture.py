from mymodule.tests import TestClass
def test_first():
    pass
class AnotherClass(object):
    def test_method(self):
        pass


 # test something

class SomeTest(TestClass):
    class_property = True

    def test_addition(self):
        def helper(a):
            return a + 1

        return self.assertEqual(helper(2), 3)


def func_test():
    pass


class ParentClassA(AnotherClass):
    class ChildClass:
        nested_property = True

        def child_method(self):
            pass

    def parent_method(self):
        pass


class AnotherIgnoredClass(object):
    def test_method(self):
        pass


@test_first
class DecoratedTestClass(TestClass):

    @test_first
    def test_me(self):
        pass


class ParentInModuleClass(mymodule.TestClass):
    def test_me(self):
        pass


class ParentClassB(TestClass):
    foo = 1

    def test_foo(self):
        pass

    def test_a(self):
        class ChildClass(object):
            nested_property = True

            def child_method(self):
                pass

            another_attribute = 'foo'

        cl = ChildClass()
        assert cl.nested_property

    def test_b(self):
        pass
