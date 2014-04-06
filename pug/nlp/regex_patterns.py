#!/usr/bin/env python
"""
Compiled Regular Expression Patterns

>>> scientific_notation_exponent.findall(' 1E10 and 1 x 10 ^23 ')
['E', 'x 10 ^']
>>> scientific_notation_exponent.findall(' 1 x 10 ^23 ')
['x 10 ^']
>>> scientific_notation_exponent.split(' 1 x 10 ** 23 ')
['1', '23']
"""

import re

nonword           = re.compile(r'[\W]')
white_space       = re.compile(r'[\s]')
scientific_notation_exponent = re.compile(r'\s*(?:[xX]{1}\s*10\s*[*^]{1,2}|[eE]){1}\s*')
not_digit_nor_sign = re.compile(r'[^0-9-+]+')

