from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'crawlnmine.views.home', name='home'),
    url(r'^miner/', include('miner.urls')),

    url(r'^admin/', include(admin.site.urls)),
)
