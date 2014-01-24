from django.conf.urls import patterns, url
from django.conf import settings
import django.views.static
#from django.views.generic import TemplateView


urlpatterns = patterns('',
    url(r'^static/(?P<path>.*)$', django.views.static.serve, { 'document_root': settings.STATIC_ROOT} ),
    url(r'^media/(?P<path>.*)$', django.views.static.serve, { 'document_root': settings.MEDIA_ROOT} ),
    #url(r'^(?P<page>.+)\.html$', StaticView.as_view()),
)
