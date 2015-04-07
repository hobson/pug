#!/usr/bin/env python
"""
Uses the unittest module to test this app with `manage.py test`.
"""

# from django.test import TestCase
from unittest import TestCase, main
import doctest
from pug.bin import push
# from pug.ann.data import weather
# from pug.ann import util


class BinDocTest(TestCase):

    def test_module(self, module=push):
        failure_count, test_count = doctest.testmod(module, raise_on_error=False, verbose=True)
        msg = "Ran {0} tests in {3} and {1} passed ({2} failed)".format(test_count, test_count-failure_count, failure_count, module.__file__)
        print msg
        if failure_count:
            # print "Ignoring {0} doctest failures...".format(__file__)
            self.fail(msg)
        # return failure_count, test_count

if __name__ == '__main__':
    main()