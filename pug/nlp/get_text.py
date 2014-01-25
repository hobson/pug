#import numpy as np
from pug.crawler.models import WikiItem


def get_text(filter_dict=None, fields=None, exclude_dict=None, table='CaseExchange', max_num_records=10):
    from collections import OrderedDict as OD
    if fields is None:
        # values in the database retrieved for assignment to values in an array of data for the fit
        fields = [
            # Name, Django ORM queryset record python expression
            'comments',
            ]
    fields = OD(fields)
    # if filter_dict is None:
    #     # subset of the BPD data to perform the multivariate linear regression on
    #     filter_dict = (('serial_number__not', 'TRUNCATED'),)
    # filter_dict = OD(filter_dict)

    qs = WikiItem.objects
    if filter_dict:
        qs = qs.filter(**filter_dict)
    if exclude_dict:
        qs = qs.exclude(**exclude_dict)
    qs = qs.values(fields).all()

    recid = 0
    for rec in qs:
        if recid >= max_num_records:
            break
        yield rec
        recid += 1
