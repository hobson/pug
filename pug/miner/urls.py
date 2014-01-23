from django.conf.urls import patterns, url
from django.conf import settings
#from django.views.generic import TemplateView
#import django.views.static


from miner.views import connections, StaticView

urlpatterns = patterns('',
    url(r'^$', 'miner.views.home', name='home'),
    url(r'^(?:chart/)?(?:[Cc]onnect(?:ion)?s?|[Gg]raph)/(?P<edges>[^/]*)', connections),
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.STATIC_ROOT} ),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.MEDIA_ROOT} ),
    url(r'^(?P<page>.+)\.html$', StaticView.as_view()),
)
