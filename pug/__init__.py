#!/usr/bin/env python
# pug packages utilities written by and for the PDX Python User's Group
#
# Copyright (C) 2013-2014  Hobson Lane <hobson@totalgood.com>
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

"""pug packages utilities written by and for the PDX Python User's Group

More information is available at https://github.com/hobsonlane/pug/
"""

# in case someone does execfile('__init__.py') so it won't make __name__ = '__main__'
__name__ = 'pug'

# the Canonical (Ubuntu) way is to define a version_info attribute
version_info = (0, 0, 7, 'alpha', 0)
__version__ = '.'.join(str(i) for i in version_info[0:3])
version_string = __version__

_github_url_ = "https://github.com/hobsonlane/%s" % (__name__)



#def test():
#    import doctest
#    return doctest.testmod(pug)

