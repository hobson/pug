from django.test import LiveServerTestCase, TestCase
from selenium import webdriver
import doctest
import pug.nlp.util 

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



class DocTest(TestCase):

    def test_doctests(self):                
        try:
            doctest.testmod(pug.nlp.util, raise_on_error=True)
        except doctest.DocTestFailure, e:
            self.fail(e)