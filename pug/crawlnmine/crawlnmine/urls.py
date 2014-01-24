from django.conf.urls import patterns, include, url

from django.contrib import admin
from pug.miner import views

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', views.home, name='home'),
    url(r'^mine/', include('pug.miner.urls', namespace='miner')),
    url(r'^crawl/', include('pug.crawler.urls', namespace='crawler')),

    url(r'^admin/', include(admin.site.urls)),
)
