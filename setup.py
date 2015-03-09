# setup.py for PUG (PDX Python User Group) package
from setuptools import find_packages
from distutils.core import setup
import io
from os.path import dirname, join

# # If you want tests to work with django settings.py you need django-setuptest
# from setuptest import test
# # If you want to use setuptest.test instead of the python test,
# #    you need to say so in your setup(kwargs) below, like this:
# # setup(cmdclass={'test': test},...

# Handy for debugging setup.py
# def setup(*args, **kwargs):
#     print('setup()   args = {0}'.format(args))
#     print('setup() kwargs = {0}'.format(kwargs))


def get_variable(relpath, keyword='__version__'):
    """Read __version__ or other properties from a python file without importing it 
    
    from gist.github.com/technonik/406623 but with added keyward kwarg """
    for line in io.open(join(dirname(__file__), relpath), encoding='cp437'):
        if keyword in line:
            if '"' in line:
                return line.split('"')[1]
            elif "'" in line:
                return line.split("'")[1]


package_name = 'pug'
init_path = join(package_name, '__init__.py')
version = get_variable(init_path)
description = get_variable(init_path, '__doc__')
__github_url__  = get_variable(init_path, '__github_url__ ')

# get_version won't parse this:
# DRY this up between here and __init__.py
__authors__ = [
    'Hobson <hobson@totalgood.com>'
    'Steve  <walkers@sharplabs.com>'
    'John   <kowalskj@sharplabs.com>'
    ]

print('Installing package named {0}. . .'.format(package_name))

import os

try:
    from pip.req import parse_requirements
    requirements = list(parse_requirements('requirements.txt'))
except:
    requirements = []
install_requires=[str(req).split(' ')[0].strip() for req in requirements if req.req and not req.url]
print('requires: %r' % install_requires)
dependency_links=[req.url for req in requirements if req.url]
print('dependcies: %r' % dependency_links)

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError, OSError):
    long_description = "Python packages implementing various natural language processing, web scraping, and predictive analytics tools developed by and for the PDX Python User Group."


EXCLUDE_FROM_PACKAGES = []

setup(
    name = package_name,
#    packages = ["pug"],  # without this: Downloading/unpacking pug ... ImportError: No module named pug ... from pug import __version__, __name__, __doc__, _github_url_
    packages=find_packages(exclude=EXCLUDE_FROM_PACKAGES),   #[package_name],  
    include_package_data = True,  # install non-.py files listed in MANIFEST.in (.js, .html, .txt, .md, etc)
    install_requires = install_requires,
    dependency_links = dependency_links,
    scripts=['pug/bin/jira.py'],
    entry_points={'console_scripts': [
        'jira = pug.crawlnmine.management:execute_from_command_line',
    ]},
    version = version,
    description = description,
    long_description = long_description or open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    author = ', '.join(__authors__),
    author_email = "admin@totalgood.com",

    #tests_require = ['django-setuptest', 'south'],
    #test_suite = 'setuptest.setuptest.SetupTestSuite',
    #cmdclass = {'test': test},
    url = __github_url__,
    # this will make setup.py use the latest github master rather than the cheeseshop tarball during installs 
    download_url = "{0}/tarball/master".format(__github_url__),
    keywords = ["agent", "bot", "ai", "crawl", "data", "science", "data science", "math", "machine-learning", "statistics", "database"],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Other Environment",
        # "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Database :: Front-Ends",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        ],
)
