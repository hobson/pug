"Django ViewSet factory."

import os.path

from django.db.models import get_app, get_models

from rest_framework import generics
from rest_framework import viewsets
from rest_framework import serializers

from pug.db import more_django_filters
from pug.nlp.util import listify

def create_model_viewsets(local, app_names=None):
    app_names = listify(app_names or os.path.basename(os.path.dirname(local.get('__file__', None))))

    for app_name in app_names:  # , 'npc_s'):
        app = get_app(app_name)
        for Model in get_models(app):

            class KitchenSinkFilter(more_django_filters.FilterSet):
                class Meta:
                    model = Model
                    # fields = tuple(f.name for f in model._meta.fields)
            # KitchenSinkFilter.__doc__ = "Filter (query) for records the database.table %s.%s\n%s" % (app_name, Model.__name__, Model.__doc__)

            class KitchenSinkSerializer(serializers.ModelSerializer):
                class Meta:
                    model = KitchenSinkFilter.Meta.model

            class KitchenSinkList(generics.ListAPIView):
                __doc__ = "Filtered list of database records (table rows) for the database.table <strong>%s.%s</strong>\n<br>\n%s" % (app_name, Model.__name__, Model.__doc__)
                model = KitchenSinkFilter.Meta.model
                serializer_class = KitchenSinkSerializer
                #filter_fields = ('acctno','whse','status','partno','date_time','reference','return_days')
                filter_class = KitchenSinkFilter
                class Meta:
                    model = Model
                    fields = tuple(f.name for f in model._meta.fields)

            KitchenSinkList.__name__ = Model.__name__ + 'List'
            # KitchenSinkList.__doc__ = "Filtered list of database records (table rows) for the database.table %s.%s\n%s" % (app_name, Model.__name__, Model.__doc__)
            local[KitchenSinkList.__name__] = KitchenSinkList


            class KitchenSinkViewSet(viewsets.ModelViewSet):
                serializer_class = KitchenSinkSerializer
                model = KitchenSinkFilter.Meta.model
                filter_fields = tuple(f.name for f in model._meta.fields)
                order_by = tuple(f.name for f in model._meta.fields)
     
            KitchenSinkViewSet.__name__ = Model.__name__ + 'ViewSet'
            # KitchenSinkViewSet.__doc__ = "A ViewSet for the database.table %s.%s\n%s" % (app_name, Model.__name__, Model.__doc__)
            local[KitchenSinkViewSet.__name__] = KitchenSinkViewSet
