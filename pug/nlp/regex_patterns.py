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

# try to make constant string variables all uppercase and regex patterns lowercase
ASCII_CHARACTERS = ''.join([chr(i) for i in range(128)])

# consider using "from re import *" and renaming this module re or RE
import re

list_bullet = re.compile(r'^\s*[! \t@#%.?(*+=-_]*[0-9.]*[#-_.)]*\s+')
nondigit = re.compile(r"[^0-9]")
nonphrase = re.compile(r"[^-\w\s/&']")
parenthetical_time = re.compile(r'([^(]*)\(\s*(\d+)\s*(?:min)?\s*\)([^(]*)', re.IGNORECASE)

nonword           = re.compile(r'[\W]')
white_space       = re.compile(r'[\s]')


# ASCII regexes from http://stackoverflow.com/a/20078869/623735
# To replace sequences of nonASCII characters with a single "?" use `nonascii_sequence.sub("?", s)`
nonascii_sequence = re.compile(r'[^\x00-\x7F]+')
# To replace sequences of nonASCII characters with a "?" per character use `nonascii.sub("?", s)`
nonascii = re.compile(r'[^\x00-\x7F]')
# To replace sequences of ASCII characters with a single "?" use `ascii_sequence.sub("?", s)`
ascii_sequence = re.compile(r'[^\x00-\x7F]+')
# To replace sequences of ASCII characters with a "?" per character use `ascii.sub("?", s)`
ascii = re.compile(r'[\x00-\x7F]')
# would be better-named as scientific_notation_base

scientific_notation_exponent = re.compile(r'\s*(?:[xX]{1}\s*10\s*[*^]{1,2}|[eE]){1}\s*')
nondigit = re.compile(r'[^\d]+')
not_digit_list = re.compile(r'[^\d,]+')
not_digit_nor_sign = re.compile(r'[^0-9-+]+')

word_sep_except_external_appostrophe = re.compile('\W*\s\'{1,3}|\'{1,3}\W+|[^-\'_.a-zA-Z0-9]+|\W+\s+')
word_sep_permissive = re.compile('[^-\'_.a-zA-Z0-9]+|[^\'a-zA-Z0-9]\s\W*')
sentence_sep = re.compile('[.?!](\W+)|$')
month_name = re.compile('(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[acbeihmlosruty]*', re.IGNORECASE)


# A permissive filter of javascript variable/function names
#  Allows unicode and leading undercores and $ 
#  From http://stackoverflow.com/a/2008444/623735
js_name = re.compile(ur'^[_$a-zA-Z\xA0-\uFFFF][_$a-zA-Z0-9\xA0-\uFFFF]*$')

# avoids special wikipedia URLs like ambiguity resolution pages
wikipedia_special = re.compile(r'.*wikipedia[.]org/wiki/[^:]+[:].*')

nones = re.compile(r'^Unk[n]?own|unk[n]?own|UNK|Unk|UNK[N]?OWN|[.]+|[-]+|[=]+|[_]+|[*]+|[?]+|N[/]A|n[/]a|None|none|NONE|Null|null|NULL|NaN$')

# Unary NOT operator and its operand returned in match.groups() 2-tuple
notter = re.compile(r'^(NOT|[\~\-\!\^])?\s*(.*)\s*$', re.IGNORECASE)