from django.test import LiveServerTestCase
from selenium import webdriver

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
        self.assertIn('start', body.text)


class AdminTest(LiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(1)

    def tearDown(self):
        self.browser.quit()

    # def test_admin_interface_login_page(self):
    #     # Angeline opens her web browser, and goes to the admin page
    #     self.browser.get(self.live_server_url + '/admin')

    #     # She sees the phrase 'Django administration' somewhere in the body
    #     body = self.browser.find_element_by_tag_name('body')
    #     self.assertIn('Django administration', body.text)
