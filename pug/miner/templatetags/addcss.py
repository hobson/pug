#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Template tag to add css class to the attributes of a field widget

Example:

{{field|addcssclass:"form-control"}}

From:
    http://vanderwijk.info/blog/adding-css-classes-formfields-in-django-templates/
"""

from django import template
register = template.Library()

@register.filter(name='addcssclass')
def addcss(field, css):
   return field.as_widget(attrs={"class":css})