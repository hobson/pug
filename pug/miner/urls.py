from django.conf.urls import patterns, include, url
#from django.conf import settings
#from django.views.generic import TemplateView
#import django.views.static
#from views import JSONView
from views import demo_linewithfocuschart, explorer


from pug.miner.views import connections, home, StaticView

urlpatterns = patterns('',
    url(r'^$', home, name='home'),
    url(r'^(?:chart/)?(?:[Cc]onnect(?:ion)?s?|[Gg]raph)/(?P<edges>[^/]*)', connections),
    url(r'^$', 'pug.miner.views.home', name='home'),
    url(r'^explorer?/$', 'pug.miner.views.explorer', name='explorer'),
    url(r'^linewithfocuschart/', 'pug.miner.views.demo_linewithfocuschart', name='demo_linewithfocuschart'),
    #url(r'^static/(?P<path>.*)$', django.views.static.serve, { 'document_root': settings.STATIC_ROOT} ),
    #url(r'^media/(?P<path>.*)$', django.views.static.serve, { 'document_root': settings.MEDIA_ROOT} ),
    #url(r'^static/(?P<page>.*)\.json$', JSONView.as_view()),
    url(r'^(?P<page>.+)\.html$', StaticView.as_view()),
)


urlpatterns += patterns('',
    url(r'^$', 'miner.views.testcele', name='testcele'),
    url(r'^do_task$', 'miner.views.do_task', name='do_task'),
    url(r'^poll_state$', 'miner.views.poll_state', name='poll_state'),

    # # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

