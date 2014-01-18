# setup.py for PUG
try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup
    from distutils.extension import Extension

from pug import __version__ as _version_
from pug import _github_url_, __name__ as _name_
import os
import sys

sys.path.insert(0, os.path.join(os.getcwd()))



# try:
#     from pip.req import parse_requirements
#     requirements = list(parse_requirements('requirements.txt'))
# except:
#     requirements = []
# install_requires=[req.name for req in requirements if req.req and not req.url]
# dependency_links=[line.url for line in requirements if line.url]


setup(
    name = _name_,
    packages = ["pug"],
    version = _version_,
    description = __doc__,
    long_description = open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    author = "Hobson Lane",
    author_email = "hobson@totalgood.com",
    url = _github_url_,
    download_url = "%s/archive/%s-%s.tar.gz" % (_github_url_, _name_, _version_),
    # download_url = _github_url_,
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
