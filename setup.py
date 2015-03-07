# setup.py for PUG (PDX Python User Group) package
from setuptools import find_packages, setup

#from distutils.core import setup
#from setuptest import test

from pug import __version__ as version
from pug import __authors__, __github_url__
from pug import __doc__ as description
from pug import __name__ as package_name

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
    download_url = "%s/archive/v%s.tar.gz" % (__github_url__, version),
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
