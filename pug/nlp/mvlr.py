from pug.crawler.models import WikiItem as Item
import numpy as np

# a [10000 x num_predictors] matrix inversion is intractible, so don't dare try it
MAX_NUM_RECORDS = 100000


def predictor_values(predictors=None, filter_dict=None, exclude_dict=None, predicted='wikiitem.modified', max_num_records=10000):
    from collections import OrderedDict as OD
    if predictors is None:
        # values in the database retrieved for assignment to values in an array of data for the fit
        predictors = (
            # Name, Django ORM queryset record python expression
            ('modified', 'title'),
            ('crawled', 'modified'),
            )
    predictors = OD(predictors)
    # if filter_dict is None:
    #     # subset of the data to perform the multivariate linear regression on
    #     filter_dict = (('serial_number__isnot', 'TRUNCATED'),)
    # filter_dict = OD(filter_dict)

    qs = Item.objects
    if filter_dict:
        qs = qs.filter(**filter_dict)
    if exclude_dict:
        qs = qs.exclude(**exclude_dict)
    qs = qs.all()

    # predictor variable values, one row for each variable, a column for each record in the queryset (value of the predictor)
    X = []

    import math

    math_env = dict([(name, getattr(math, name, lambda x: x)) for name in math.__dict__ if not name.startswith('__')])
    blacklist = ['credits', 'del', 'delattr', 'dir', 'dreload', 'file', 'frozenset', 'get_ipython', 'make_option', 'os', 'sys', 'eval', 'globals', 'locals', 'open', 'exec', 'execfile']
    whitelist = ['sum', 'pow', 'float', 'int', 'floor', 'len', 'list', 'max', 'min', 'oct', 'ord', 'tuple', 'dict', 'str', 'unicode', 'type', 'isinstance', 'hex', 'ord', 'hash']
    global_env = dict([(name, __builtins__.get(name, lambda x: x)) for name in __builtins__ if name in whitelist and name not in blacklist and not name.startswith('__')])

    safe_env = {
        "locals": None,
        "globals":  None,
        "__name__": None,
        "__file__": None,
        "__builtins__": None,
        }

    safe_env.update(global_env)
    safe_env.update(math_env)

    N = min(max_num_records, qs.count(), MAX_NUM_RECORDS)
    y = []

    for record in qs[:N]:
        X += [[]]
        for name, expression in predictors.iteritems():
            safe_env['case'] = record
            X[-1] += [eval(expression, safe_env)]
        y += [eval(predicted, safe_env)]

    return X, y


def compute_fit(predictor_matrix, predicted_values):
    A = np.matrix(predictor_matrix)
    y = np.hstack(predicted_values)
    beta = np.linalg.lstsq(A, y)
    return beta


def demo():
    import nlp.plotter
    A, y = predictor_values()
    beta, residuals, rank, singular_values = compute_fit(A, y)
    nlp.plotter.regressionplot(A, y, (beta, residuals, rank, singular_values))
