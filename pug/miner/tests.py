from django.test import LiveServerTestCase #, TestCase
from selenium import webdriver
#import pug.nlp.util
#import pug.nlp.djdb


class HomeTest(LiveServerTestCase):

    def setUp(self):
        self.page = webdriver.Firefox()
        self.page.implicitly_wait(1)

    def tearDown(self):
        self.page.quit()

    def test_home_page(self):
        # User opens web browser, and goes to the home (root url) page
        self.page.get(self.live_server_url + '/')

        # She sees an HTML page that has a body tag with some non-empty string within it
        body = self.page.find_element_by_tag_name('body')
        self.assertTrue(bool(body.text))

    def test_dashboard(self):
        # User browses to dashboard URL
        self.page.get(self.live_server_url + '/dashboard')

        # HTML page with more than 1 SVG element and more than 100 bytes for the first 2 plots
        plots = self.page.find_elements_by_tag_name('svg')
        # self.assertGreater(len(plots), 1)

        # line chart with at least some text
        # self.assertGreater(len(plots[0].text), 50)

        # bar chart with at least some text
        # self.assertGreater(len(plots[1].text), 50)

        bars = self.page.find_elements_by_css_selector('rect.bar')

        # HTML page with more than 6 rect elements classed "bar"
        # self.assertGreater(len(bars), 5)

class AdminTest(LiveServerTestCase):
    pass
    # def setUp(self):
    #     self.page = webdriver.Firefox()
    #     self.page.implicitly_wait(1)

    # def tearDown(self):
    #     self.page.quit()

    # def test_admin_interface_login_page(self):
    #     # Angeline opens her web page, and goes to the admin page
    #     self.page.get(self.live_server_url + '/admin')

    #     # She sees the phrase 'Django administration' somewhere in the body
    #     body = self.page.find_element_by_tag_name('body')
    #     self.assertIn('Django administration', body.text)


# Django 1.7 recommends following following python 2.4 unittest+doctest recommendations
#  https://docs.djangoproject.com/en/dev/releases/1.6/#new-test-runner
#  https://docs.python.org/2/library/doctest.html#unittest-api
# import unittest
# import doctest

# def load_tests(loader, tests, ignore):
#     # tests.addTests(doctest.DocTestSuite(pug.nlp.util))
#     #return tests
#     return []


# # This was clunky...

# class DocTest(TestCase):

#     def test_util(self, module=pug.nlp.util):
#         failure_count, test_count = doctest.testmod(module, raise_on_error=False, verbose=True)
#         msg = "Ran {0} tests in {3} and {1} passed ({2} failed)".format(test_count, test_count-failure_count, failure_count, module.__file__)
#         print msg
#         if failure_count:
#             print "Ignoring pug.nlp.util doctest failures..."
#             #self.fail(msg)

#     def test_djdb(self, module=pug.nlp.djdb):
#         failure_count, test_count = doctest.testmod(module, raise_on_error=False, verbose=True)
#         msg = "Ran {0} tests in {3} and {1} passed ({2} failed)".format(test_count, test_count-failure_count, failure_count, module.__file__)
#         print msg
#         if failure_count:
#             print "Ignoring pug.nlp.djdb doctest failures..."
#             # self.fail(msg)
