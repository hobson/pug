import os
# Explicitly declare some header/meta information (about `pug`)
#  rather than allowing python to populate them automatically.
# This allows simple parsers (in setup.py) to extract them
#  without importing this file or __init__.py

__package__ = 'pug'
__package_path__ = os.path.abspath('.')

def try_read(filename, path=__package_path__):
    try:
        return open(os.path.join(path, '..', filename), 'r').read()
    except:
        try:
            return open(filename, 'r').read()
        except:
            return None


__version__ = '0.1.5'
# __name__ = __package__
__license__ = try_read('LICENSE.txt', __package_path__)
__doc__ = try_read('README.md', __package_path__)
__author__ = "Hobson <hobson@totalgood.com>"
__authors__ = (
    "Hobson <hobson@totalgood.com>",
    "Steve <walkers@sharplabs.com>",
    "John <kowalskj@sharplabs.com>",
    "Low <kianseong@gmail.com>",
    )
__url__ = "https://github.com/hobson/{0}".format(__package__)

