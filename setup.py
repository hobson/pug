#!/usr/bin/env python
''' The PUG namespace package (meta package) depends on all the pug-* packages
    collection. As a result, installing it vith `pip` or `easy_install` also installs:
    + pug-nlp    Natural Language and Text-Processing utilities
    + pug-ann    Artificial Neural Network utilities for the pybrain package
    - pug-djdb   Django utilities and webapps for crawling and mining for data
    - pug-invest Utilities for predictivie analytics on time series data (including financial data)
    - pug-bin    Dev-Ops scripts (some shell/bash, but mostly python)
'''
# from setuptools import find_packages
from distutils.core import setup
import os

# setup.py for PUG (PDX Python User Group) package

# the parent name (perhaps a namespace package) you'd import
__namespace_package__ = 'pug'
# the subpackage that this installer is providing that you'd import like __import__(__namespace_package__ + '.' + '__subpackage__')
__subpackage__ = ''

# the name as it will appear in the pypi cheeseshop repository, not the name you'd use to import it
project_name = '{}'.format(__namespace_package__) + ('-' + __subpackage__ if __subpackage__ else '')
# the full import name
package_name = '{}'.format(__namespace_package__) + ('.' + __subpackage__ if __subpackage__ else '')

global_env, env = {}, {}
execfile(os.path.join(project_name, 'package_info.py'), global_env, env)

print('Found package info: {}'.format(env))

version = env.get('__version__', '0.0.1')
package_docstring = env.get('__doc__', '`{}` python package'.format(project_name))
description = package_docstring.split('\n')[0]
long_description = package_docstring
__url__  = env.get('__url__', 'http://github.com/hobson/')
__authors__  = env.get('__authors__', ('Hobson <hobson@totalgood.com>',))
try:
    long_description = open('README.rst', 'r').read()
except:  # (IOError, ImportError, OSError, RuntimeError):
    print('WARNING: Unable to find README.rst.')

print('Installing package named {} pointed at url {}. . .'.format(project_name, __url__))

setup(
    name = project_name,
    version = version,
#    url = __url__,
    description = 'Meta package to install the PDX Python User Group utilities.',
    long_description = long_description,
    author = 'Hobson Lane',
    author_email = 'admin@totalgood.com',
    include_package_data = True,  # install non-.py files listed in MANIFEST.in (.js, .html, .txt, .md, etc)
    license = 'MIT',
    platforms = '',
    # enable the command-line script `push.py 'message'`
    scripts=[
        'pug/bin/push.py',
        'pug/bin/install_requirements',
        ],
    # # enable the command-line script `push 'message'`
    # entry_points={'console_scripts': [
    #      'push=pug.bin.push:main',
    # ]},
    #install_requires = install_requires,
    #dependency_links = dependency_links,
    install_requires = [
        'pug-nlp',
        'pug-ann',
        # 'pug-invest',
        # 'pug-djdb',
        # 'pub-bin',
    ],
    #     # Force setup.py to use the latest github master source files rather than the cheeseshop tarball: 
    # download_url = "{}/tarball/master".format(__url__),
    keywords = ["natural language processing", "text processing", "neural net", "science", "data science", "math", "machine-learning", "statistics", "database"],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        ]
)
