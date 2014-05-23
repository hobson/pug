from django.conf.urls import patterns, url  #, include
#from django.conf import settings
#from django.views.generic import TemplateView
#import django.views.static
#from views import JSONView
import views

urlpatterns = patterns('',
    #url(r'^$', home, name='home'),
    #url(r'^(?:chart/)?(?:[Cc]onnect(?:ion)?s?|[Gg]raph)/(?P<edges>[^/]*)', views.connections, name='connections'),
    url(r'^$', views.home, name='home'),
    url(r'^explorer?/', views.explorer, name='explorer'),
    url(r'^lag[-]?(cmf|pmf|cdf|hist)?/', views.lag, name='lag'),
    url(r'^hist[-]?(cmf|pmf|cdf|hist)?/', views.hist, name='hist'),
    #url(r'^static/(?P<path>.*)$', django.views.static.serve, { 'document_root': settings.STATIC_ROOT} ),
    #url(r'^media/(?P<path>.*)$', django.views.static.serve, { 'document_root': settings.MEDIA_ROOT} ),
    #url(r'^static/(?P<page>.*)\.json$', JSONView.as_view()),
    url(r'^(?P<page>.+)\.html$', views.StaticView.as_view(), name='StaticView'),
)


# urlpatterns += patterns('',
#     url(r'^$', views.testcele, name='testcele'),
#     url(r'^do_task$', views.do_task, name='do_task'),
#     url(r'^poll_state$', views.poll_state, name='poll_state'),

#     # # Uncomment the next line to enable the admin:
#     # url(r'^admin/', include(admin.site.urls)),
# )

