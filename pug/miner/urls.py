from django.conf.urls import patterns, url  #, include
#from django.conf import settings
#from django.views.generic import TemplateView
#import django.views.static
#from views import JSONView
import pug.miner.views

urlpatterns = patterns('',
    #url(r'^$', home, name='home'),
    url(r'^(?:chart/)?(?:[Cc]onnect(?:ion)?s?|[Gg]raph)/(?P<edges>[^/]*)', pug.miner.views.connections, name='miner-connections'),
    url(r'^$', pug.miner.views.home, name='miner-home'),
    url(r'^explorer?/', pug.miner.views.explorer, name='miner-explorer'),
    url(r'^lag-?(cmf|pmf|cdf|hist)?/', pug.miner.views.lag, name='miner-lag'),
    #url(r'^static/(?P<path>.*)$', django.views.static.serve, { 'document_root': settings.STATIC_ROOT} ),
    #url(r'^media/(?P<path>.*)$', django.views.static.serve, { 'document_root': settings.MEDIA_ROOT} ),
    #url(r'^static/(?P<page>.*)\.json$', JSONView.as_view()),
    url(r'^(?P<page>.+)\.html$', pug.miner.views.StaticView.as_view(), name='miner-StaticView'),
)


urlpatterns += patterns('',
    url(r'^$', pug.miner.views.testcele, name='testcele'),
    url(r'^do_task$', pug.miner.views.do_task, name='do_task'),
    url(r'^poll_state$', pug.miner.views.poll_state, name='poll_state'),

    # # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

