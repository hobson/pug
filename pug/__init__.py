# Copyright (C) 2012-2014  Hobson Lane <hobson@totalgood.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""pug -- Package of Utilities written by and for the PDX Python User's Group"""

__version__ = '0.1.0'
__name__='pug'
__doc__='Python Utilities by and for the PDX Python User Group'
__authors__ = [
    'Hobson <hobson@totalgood.com>'
    'Steve  <walkers@sharplabs.com>'
    'John   <kowalskj@sharplabs.com>'
    ]
__github_url__ = "https://github.com/hobson/%s" % (__name__)

# # FIXME: This doesn't work:
# #        >>> import pug
# #        >>> pug.nlp.util.reduce_vocab(('on', 'hon', 'honey')) 
# # FIXME: But setup will fail if you import submodules here (no dependencies installed before checking __version__)!
import ann
# import ann.util
import data
import data.weather
import nlp
import nlp.util
import invest
import invest.util
import db
__all__ = ['ann', 'data', 'data.weather', 'nlp', 'nlp.util', 'invest', 'invest.util', 'db']
