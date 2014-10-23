from django.test import LiveServerTestCase, TestCase
from selenium import webdriver
import doctest
import pug.nlp.util
import pug.nlp.djdb

class HomeTest(LiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(1)

    def tearDown(self):
        self.browser.quit()

    def test_home_page(self):
        # Angeline opens her web browser, and goes to the home (root url) page
        self.browser.get(self.live_server_url + '/')

        # She sees the word start somewhere
        body = self.browser.find_element_by_tag_name('body')
        self.assertTrue(bool(body.text))


class AdminTest(LiveServerTestCase):
    pass
    # def setUp(self):
    #     self.browser = webdriver.Firefox()
    #     self.browser.implicitly_wait(1)

    # def tearDown(self):
    #     self.browser.quit()

    # def test_admin_interface_login_page(self):
    #     # Angeline opens her web browser, and goes to the admin page
    #     self.browser.get(self.live_server_url + '/admin')

    #     # She sees the phrase 'Django administration' somewhere in the body
    #     body = self.browser.find_element_by_tag_name('body')
    #     self.assertIn('Django administration', body.text)



# class DocTest(TestCase):

#     def test_util(self, module=pug.nlp.util):
#         failure_count, test_count = doctest.testmod(module, raise_on_error=False, verbose=True)
#         msg = "Ran {0} tests in {3} and {1} passed ({2} failed)".format(test_count, test_count-failure_count, failure_count, module.__file__)
#         print msg
#         if failure_count:
#             self.fail(msg)

#     def test_djdb(self, module=pug.nlp.djdb):
#         failure_count, test_count = doctest.testmod(module, raise_on_error=False, verbose=True)
#         msg = "Ran {0} tests in {3} and {1} passed ({2} failed)".format(test_count, test_count-failure_count, failure_count, module.__file__)
#         print msg
#         if failure_count:
#             self.fail(msg)