# setup.py for PUG
from distutils.core import setup
#from setuptest import test

from pug import __version__, __authors__, __github_url__
from pug import __name__ as package_name
import os
# import sys

# sys.path.insert(0, os.path.join(os.getcwd()))

try:
    from pip.req import parse_requirements
    requirements = list(parse_requirements('requirements.txt'))
except:
    requirements = []
install_requires=[str(req).split(' ')[0].strip() for req in requirements if req.req and not req.url]
print 'requires: %r' % install_requires
dependency_links=[req.url for req in requirements if req.url]
print 'dependcies: %r' % dependency_links


setup(
    name = package_name,
    packages = ["pug"],  # without this: Downloading/unpacking pug ... ImportError: No module named pug ... from pug import __version__, __name__, __doc__, _github_url_
    include_package_data = True,  # install non-.py files listed in MANIFEST.in (.js, .html, .txt, .md, etc)
    install_requires = install_requires,
    dependency_links = dependency_links,
    version = __version__,
    description = __doc__,
    long_description = open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    author = ', '.join(__authors__),
    author_email = "pugauthors@totalgood.com",
    #tests_require = ['django-setuptest', 'south'],
    #test_suite = 'setuptest.setuptest.SetupTestSuite',
    #cmdclass = {'test': test},
    url = __github_url__,
    download_url = "%s/archive/v%s.tar.gz" % (__github_url__, __version__),
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
