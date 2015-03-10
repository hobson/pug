"""
Uses the unittest module to test this app with `manage.py test`.
"""

from django.test import TestCase
import doctest


# class PuffinTest(TestCase):
#     from puffin_lsa import PuffinLSA
#     from examples import titles

#     def setUp(self):
#         self.docs = titles
#         self.lsa = PuffinLSA()

#         for txt in docs:
#             lsa.parse(txt)

#     def test_puffin(self):
#         """
#         Tests that puffin LSA algorithm works on the set of example titles they gave.
#         """
#         self.lsa.build()
#         # self.lsa.printA()
#         self.lsa.calc()
#         # lsa.printSVD()

#         self.assertEqual(lsa.S, )

from doctest import testmod
import nlp
import nlp.util


# from collections import OrderedDict as OD

class NLPTest(TestCase):

    def setUp(self):
        self.tobes_data = nlp.examples.tobes_data
        self.dt = nlp.decision_tree
        self.field = 'comments'
        self.uniques = [sorted(self.dt.count_unique(self.tobes_data, i).values()) for i in range(len(self.tobes_data[0]))]
        self.expected_uniques = [[2, 3, 3, 3, 5], [2, 4, 4, 6], [8, 8], [2, 2, 2, 3, 3, 4], [3, 6, 7]]

    def test_tobes_data(self):
        """
        Tests that puffin LSA algorithm works on the set of example titles they gave.
        """
        T, F = self.dt.divide(self.tobes_data, 2, 'yes')

        self.assertEqual(len(tuple(T)), 8)
        self.assertEqual(len(tuple(F)), 8)

        for i in range(5):
            self.assertEqual(self.uniques[i], self.expected_uniques[i])
            self.assertEqual(sum(self.uniques[i]), 16)

        for module in nlp.modules:
            failure_count, test_count = testmod(module)
            self.assertEqual(failure_count, 0, msg='doctest.testmod(%s) had %s/%s failures' % (module, failure_count, test_count))
            self.assertGreater(test_count, 1, msg='doctest.testmod(%s) had %s/%s failures (too few tests)' % (module, failure_count, test_count))


class NLPDocTest(TestCase):

    def test_module_doctests(self, module=nlp.util):
        failure_count, test_count = doctest.testmod(module, raise_on_error=False, verbose=True)
        msg = "Ran {0} tests in {3} and {1} passed ({2} failed)".format(test_count, test_count-failure_count, failure_count, module.__file__)
        print msg
        if failure_count:
            # print "Ignoring {0} doctest failures...".format(__file__)
            self.fail(msg)