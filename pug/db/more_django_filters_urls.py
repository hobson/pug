"append more urls to the urlconf tuple for all the model filters in more_django_filters"

from django.db.models import get_app, get_models
from django.conf.urls import url, patterns

#from pug.db import more_django_filters
from pug.nlp.util import listify

def append_urls(urlpatterns, app_names):
    app_names = listify(app_names) or []

    for app_name in app_names:  # , 'npc_s'):
        views_name = app_name + '.views'
        app_module = __import__(views_name)
        app = get_app(app_name)
        for Model in get_models(app):
            model_name = Model.__name__
            View = app_module.views.__dict__[model_name + 'List']
            urlpatterns += patterns('', url(r'^' + app_name + r'/' + model_name, View.as_view()))#, name='order-list'),)

    return urlpatterns
