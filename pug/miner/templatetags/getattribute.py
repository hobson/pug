#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Template tag filter that runs .getattr and .get on an object.

Allows the template to retrieve a value from an object, dict, or list
using a string attribute name, key value, or numerical array index.

Example:

{% load getattribute %}
{{ object|getattribute:dynamic_string_var }}

From:
    [Stack Overflow](http://stackoverflow.com/a/1112236/623735] by [fotinakis](http://stackoverflow.com/users/128597/fotinakis)
"""

import re
from django import template
from django.conf import settings

numeric_test = re.compile("^\d+$")
register = template.Library()

def getattribute(value, arg):
    """Gets an attribute of an object dynamically from a string name"""

    if hasattr(value, str(arg)):
        return getattr(value, arg)
    elif hasattr(value, 'has_key') and value.has_key(arg):
        return value[arg]
    elif numeric_test.match(str(arg)) and len(value) > int(arg):
        return value[int(arg)]
    else:
        return settings.TEMPLATE_STRING_IF_INVALID

register.filter('getattribute', getattribute)