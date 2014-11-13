from django.conf.urls import patterns, url  #, include
#from django.conf import settings
#from django.views.generic import TemplateView
#import django.views.static
#from views import JSONView
import views

urlpatterns = patterns('',
    url(r'^plot/(?P<symbols>[A-Z,$]+)$', views.PlotSymbolView.as_view()),
)
