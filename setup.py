# setup.py for PUG (PDX Python User Group) package
# the parent name (perhaps a namespace package) you'd import
__namespace_package__ = 'pug'
# the subpackage that this installer is providing that you'd import like __import__(__namespace_package__ + '.' + '__subpackage__')
__subpackage__ = ''
# the name as it will appear in the pypi cheeseshop repositor, not the name you'd use to import it
project_name = '{}'.format(__namespace_package__) + ('-' + __subpackage__ if __subpackage__ else '')
package_name = '{}'.format(__namespace_package__) + ('.' + __subpackage__ if __subpackage__ else '')

from setuptools import find_packages
from distutils.core import setup
import os

# # If you want tests to work with django settings.py you need django-setuptest
# from setuptest import test
# # If you want to use setuptest.test instead of the python test,
# #    you need to say so in your setup(kwargs) below, like this:
# # setup(cmdclass={'test': test},...

print('Installing package named {} from the {} project, a sub-package/project of the namespace package {}. . .'.format(package_name, project_name, package_name))

global_env, env = {}, {}
package_info_path = os.path.join(__subpackage__, 'package_info.py')
if __namespace_package__:
    package_info_path = os.path.join(__namespace_package__, package_info_path)
# FIXME: import this by path instead of executing it
execfile(package_info_path, global_env, env)
print('Found package info in {}: {}'.format(package_info_path, env))

version = env.get('__version__', '0.0.1')
package_docstring = env.get('__doc__', '`{}` python package'.format(project_name))
description = package_docstring.split('\n')[0]
long_description = package_docstring
__url__  = env.get('__url__', 'http://github.com/hobson/')
__authors__  = env.get('__authors__', ('Hobson <hobson@totalgood.com>',))
try:
    long_description = open('README.rst', 'r').read()
except:  # (IOError, ImportError, OSError, RuntimeError):
    print('WARNING: Unable to find or read README.rst.')


dependency_links = [] #  ['http://github.com/hobson/pug-nlp/tarball/master#egg=pug-nlp-master'] 
EXCLUDE_FROM_PACKAGES = []


print('Installing package named {} from the {} project. . .'.format(package_name, project_name))
packages = list(set([package_name] + list(find_packages(exclude=EXCLUDE_FROM_PACKAGES))))
print('Packages being installed: {}'.format(packages))


# sudo yum install libjpeg-devel openjpeg-devel
install_requires = [
    'wsgiref==0.1.2',
    'six==1.9.0',
#    'setuptools>=14.3',
    'pyzmq==14.5.0',
    'Unidecode==0.4.16',
    'cffi==0.8.6',
    'chardet==2.3.0',
    'pyOpenSSL==0.14',
    'pytz==2015.2', 
    'python-dateutil==2.4.1',
    'pandas>=0.15.2',
    'xlrd==0.9.3', 'Pillow==2.7',
    'fuzzywuzzy==0.5.0',
    'python-Levenshtein==0.12.0',
    'progressbar2==2.7.3',
    'python-slugify==0.1.0',
    'matplotlib==1.4.3',
    'numpy==1.9.2',
    'scipy>=0.15.1',
    'pybrain>=0.3.3',

    'pug-nlp>=0.0.17',
    'pug-ann>=0.0.17',
    'pug-invest>=0.0.17',
    ]
print('install_requires: {}'.format(install_requires))


setup(
    name=project_name,
    packages=packages,
    namespace_packages=[__namespace_package__],

    # install non-.py files listed in MANIFEST.in (.js, .html, .txt, .md, etc)
    include_package_data = True,
    install_requires = install_requires,
    dependency_links = dependency_links,
    # enable the command-line script `push.py 'message'`
    scripts=[
        'pug/bin/push.py',
        'pug/bin/install_requirements',
        ],
    # enable the command-line script `push 'message'`
    entry_points={'console_scripts': [
         'push=pug.bin.push:main',
    ]},
    version = version,
    description = description,
    long_description = long_description,
    author = ', '.join(__authors__),
    author_email = __authors__[0].split('<')[1].strip().strip('>'),

    #tests_require = ['django-setuptest', 'south'],
    #test_suite = 'setuptest.setuptest.SetupTestSuite',
    #cmdclass = {'test': test},
    # this would install the master branch from github
    # url = __url__,

    # Force setup.py to use the latest github master source files rather than the cheeseshop tarball: 
    download_url = "{}/tarball/master".format(__url__),
    keywords = ["nlp", "natural language processing", "text", "text processing", "bot", "ai", "agent", "data", "science", "data science", "math", "machine-learning", "statistics", "database"],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Other Environment",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        ],
)
