from django.conf.urls import patterns, include, url

from django.contrib import admin
from pug.miner import views

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', views.home, name='home'),
    #url(r'^miner/', include('pug.miner.urls')),

    url(r'^admin/', include(admin.site.urls)),
)
