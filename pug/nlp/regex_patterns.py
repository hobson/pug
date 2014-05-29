#!/usr/bin/env python
"""
Compiled Regular Expression Patterns

>>> scientific_notation_exponent.split(' 1 x 10 ** 23 ')
['1', '23']
>>> scientific_notation_exponent.split(' 1E10 and 1 x 10 ^23 ')
[' 1', '10 and 1', '23 ']
>>> scientific_notation_exponent.findall(' 1 x 10 ^23 ')
['x 10 ^']
>>> scientific_notation_exponent.findall(' 1E10 and 1 x 10 ^23 ')
['E', 'x 10 ^']
"""

# consider using "from re import *" and renaming this module re or RE
import re

nonword           = re.compile(r'[\W]')
white_space       = re.compile(r'[\s]')
# would be better-named as scientific_notation_base
scientific_notation_exponent = re.compile(r'\s*(?:[xX]{1}\s*10\s*[*^]{1,2}|[eE]){1}\s*')
not_digit_nor_sign = re.compile(r'[^0-9-+]+')

word_sep_except_external_appostrophe = re.compile('\W*\s\'{1,3}|\'{1,3}\W+|[^-\'_.a-zA-Z0-9]+|\W+\s+')
word_sep_permissive = re.compile('[^-\'_.a-zA-Z0-9]+|[^\'a-zA-Z0-9]\s\W*')
sentence_sep = re.compile('[.?!](\W+)|$')
month_name = re.compile('(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[acbeihmlosruty]*', re.IGNORECASE)
not_digit_list = re.compile(r'[^\d,]+')

# A permissive filter of javascript variable/function names
#  Allows unicode and leading undercores and $ 
#  From http://stackoverflow.com/a/2008444/623735
js_name = re.compile(r'^[_$a-zA-Z\xA0-\uFFFF][_$a-zA-Z0-9\xA0-\uFFFF]*$')

# avoids special wikipedia URLs like ambiguity resolution pages
wikipedia_special = re.compile(r'.*wikipedia[.]org/wiki/[^:]+[:].*')