from mymodule.tests import TestClass


class AnotherClass(object):
    def test_method(self):
        assert True


 # test something

class SomeTest(TestClass):
    class_property = True

    def test_addition(self):
        def helper(a):
            return a + 1

        return self.assertEqual(helper(2), 3)


def func_test():
    assert 1
