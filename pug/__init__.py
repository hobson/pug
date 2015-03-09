"""pug -- Package of Utilities written by and for the PDX Python User's Group"""


from package_info import __license__, __version__, __name__, __doc__, __author__, __authors__
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
import nlp
import nlp.util
import invest
import invest.util
import db
__all__ = ['ann', 'data', 'data.weather', 'nlp', 'nlp.util', 'invest', 'invest.util', 'db']
