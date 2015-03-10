#from django.test.simple import DjangoTestSuiteRunner


class NullTestRunner(object):
    """ A test runner to test without database creation or automatic test*.py discovery"""

    def run_tests(self, *args, **kwargs):
        """Override the running of tests entirely (including discovery, and DB maintenance)"""
        pass
    
    def setup_databases(self, **kwargs):
        """ Override the database creation defined in parent class """
        pass

    def teardown_databases(self, old_config, **kwargs):
        """ Override the database teardown defined in parent class """
        pass