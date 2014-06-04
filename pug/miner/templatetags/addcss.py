#!/usr/bin/env python
# -*- coding: utf-8 -*-
# from http://vanderwijk.info/blog/adding-css-classes-formfields-in-django-templates/

from django import template
register = template.Library()

@register.filter(name='addcss')
def addcss(field, css):
   return field.as_widget(attrs={"class":css})