import string

printable   = string.printable
uppercase   = string.uppercase
letters     = string.letters
digits      = string.digits
punctuation = string.punctuation
whitespace  = string.whitespace

printable_uppercase = digits + uppercase + '!"#$%&\'()*+,-./:;<= >?@[\\]^_`{|}~ \t\n\r\x0b\x0c'
uppercase_ascii  = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./0123456789:;<= >?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`{|}~\x7f'
ascii            = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./0123456789:;<= >?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\x7f'
# PUNCTUATION_RE_CLASS = r'[-\+' + string.punctuation.replace('-', '') + r']'  # FIXME: duplicates "+" and seems wrong (don't other punctuation symbols need escaping?)
not_digits                    = letters + punctuation + whitespace
not_digits_nor_sign            = not_digits.replace('-', '').replace('+', '')
not_digits_nor_decimal         = not_digits.replace('.', '')
not_digits_nor_sign_but_with_decimal = not_digits_nor_sign.replace('.', '')

