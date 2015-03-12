"""pug -- Package of Utilities written by and for the PDX Python User's Group"""
from pkg_resources import declare_namespace
declare_namespace(__name__)

# from package_info import __license__, __version__, __doc__, __author__, __authors__

# from pkgutil import extend_path
# __path__ = extend_path(__path__, __package__)


# __authors__ = (
#     "Hobson <hobson@totalgood.com>",
#     "Steve <walkers@sharplabs.com>",
#     "John <kowalskj@sharplabs.com>",
#     "Low <kianseong@gmail.com>",
#     )
# __github_url__ = "https://github.com/hobson/{0}".format(__name__)

import ann
import ann.util
import data
import data.weather
# import nlp
# import nlp.util
import invest
import invest.util
# import db
# import test
# import test.runner
__all__ = ['ann', 'ann.util', 'data', 'data.weather', 'nlp', 'nlp.util', 'invest', 'invest.util', 'db', 'test', 'test.runner']
