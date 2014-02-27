"append more urls to the urlconf tuple for all the model filters in more_django_filters"

from os.path import basename, dirname

from django.db.models import get_app, get_models
from django.conf.urls import url, patterns, include

#from pug.db import more_django_filters
from pug.nlp.util import listify

def append_urls(local, app_names=None):
    app_names = listify(app_names or basename(dirname(local.get('__file__', None))))
    urlpatterns = local.get('urlpatterns', patterns(''))

    for app_name in app_names:
        views_name = app_name + '.views'
        app_module = __import__(views_name)
        app = get_app(app_name)
        for Model in get_models(app):
            model_name = Model.__name__
            View = app_module.views.__dict__[model_name + 'List']
            urlpatterns += patterns('', url(r'^' + app_name + r'/' + model_name, View.as_view()))#, name='order-list'),)

    local['urlpatterns'] = urlpatterns


def append_app_urls(local, app_names):
    app_names = listify(app_names)  # or local.get('local.settings.INSTALLED_APPS') ;)
    urlpatterns = local.get('urlpatterns', patterns(''))

    for app_name in app_names:
        urlpatterns += patterns('', url(r'^', include('%s.urls' % app_name)))#, name='order-list'),)
    local['urlpatterns'] = urlpatterns
