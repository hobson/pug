# test.py
from unittest import TestCase, main
import doctest

class PassTest(TestCase):

    def test_module(self, module=None):
        if not module:
            return
        failure_count, test_count = doctest.testmod(module, raise_on_error=False, verbose=True)
        msg = "Ran {0} tests in {3} and {1} passed ({2} failed)".format(test_count, test_count-failure_count, failure_count, module.__file__)
        print msg
        if failure_count:
            # print "Ignoring {0} doctest failures...".format(__file__)
            self.fail(msg)
        # return failure_count, test_count

if __name__ == '__main__':
    main()

