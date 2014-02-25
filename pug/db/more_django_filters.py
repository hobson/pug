#from django_filters import NumberFilter, CharFilter, BooleanFilter, DateTimeFilter
from django_filters.filters import NumberFilter, CharFilter, BooleanFilter, DateTimeFilter
from django.db.models import fields as django_field_types
from django_filters.filterset import get_declared_filters, FilterSetOptions, models, get_model_field, filters_for_model, BaseFilterSet
from django.utils import six
#from django.db import models

filter_field_type = {
    django_field_types.IntegerField: NumberFilter,
    django_field_types.FloatField: NumberFilter,
    django_field_types.DecimalField: NumberFilter,
    django_field_types.CharField: CharFilter,
    django_field_types.TextField: CharFilter,
    django_field_types.BooleanField: BooleanFilter,
    django_field_types.NullBooleanField: BooleanFilter,
    #django_field_types.DateField: DateFilter,
    django_field_types.DateTimeField: DateTimeFilter,
    }
# TODO: different subsets of these within each of the filter types above
filter_suffixes = ('lt', 'lte', 'gt', 'gte', 'startswith', 'istartswith', 'endswith', 'iendswith', 'year', 'month', 'week_day', 'isnull')


class KitchenSinkFilterSetMetaclass(type):
    def __new__(cls, name, bases, attrs):
        try:
            parents = [b for b in bases if issubclass(b, FilterSet)]
        except NameError:
            # We are defining FilterSet itself here
            parents = None
        declared_filters = get_declared_filters(bases, attrs, False)
        new_class = super(
            KitchenSinkFilterSetMetaclass, cls).__new__(cls, name, bases, attrs)

        if not parents:
            return new_class

        opts = new_class._meta = FilterSetOptions(
            getattr(new_class, 'Meta', None))
        if opts.model:
            filters = kitchen_sink_filters_for_model(opts.model, opts.fields, opts.exclude,
                                        new_class.filter_for_field,
                                        new_class.filter_for_reverse_field)
            filters.update(declared_filters)
        else:
            filters = declared_filters

        if None in filters.values():
            raise TypeError("Meta.fields contains a field that isn't defined on this FilterSet")

        new_class.declared_filters = declared_filters
        new_class.base_filters = filters
        return new_class


def kitchen_sink_filters_for_model(model, fields=None, exclude=None, filter_for_field=None, filter_for_reverse_field=None):
    if fields is None:
        fields = [field.name for field in sorted(model._meta.fields + model._meta.many_to_many) if not isinstance(field, models.AutoField)]
    # poor-man's inheritance, call the "parent's" method
    field_dict = filters_for_model(model, fields=fields, exclude=exclude, filter_for_field=filter_for_field, filter_for_reverse_field=filter_for_reverse_field)

    # This is where the kitchen_sink gets stapled on
    for field_name in fields:  # model._meta.fields:
        if exclude is not None and field_name in exclude:
            continue
        field = get_model_field(model, field_name)
        if field is None:
            # field_dict[f] = None
            continue
        # Nervous about using hash key lookup instead of isinstance()
        # The django_types in the dict may be the parents of the intended set of field types 
        for django_type, filter_type in filter_field_type.iteritems():
            if isinstance(field, django_type):
                # FIXME: `filter_suffixes` should be a list within the dict, one for each django_type
                for suffix in filter_suffixes:               
                            # filter_for_field(name...)  <-- would be better to use this ?(see filterset use)
                    filter_ = filter_type(name=field.name, lookup_type=suffix)
                    if filter_:
                        field_dict[field_name + '__' + suffix] = filter_

    return field_dict


class FilterSet(six.with_metaclass(KitchenSinkFilterSetMetaclass, BaseFilterSet)):
    pass
