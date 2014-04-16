# decision tree for DB record classification
# attempts to identify cases that result in a service call

from examples import tobes_data
import datetime

from pug.db.explore import count_unique


def divide(qs, field, target=0, default=0, ignore_fields=None, include_fields=None):
    if ignore_fields is None:
        ignore_fields = ('id', 'pk')
    judge = None
    # TODO: DRY this up! Could make judges a dict with (type, type) as keys. See git branch 'unlambda'

    # row is a django model db record (model instance?)
    if isinstance(target, (int, float, bool, datetime.datetime, datetime.date)):
        judge = '__gte'
    elif isinstance(target, (tuple, list, dict, set)):
        judge = '__in'
    else:
        judge = ''

    kwargs = { '%s%s' % (field, judge): target }

    if include_fields:
        include_fields = [f for f in include_fields if f not in ignore_fields]
        qs = qs.values(*include_fields)
    true_qs = qs.filter(**kwargs)
    false_qs = qs.exclude(**kwargs)
    
    return (true_qs, false_qs)



def gini_impurity(qs, field):
    '''Gini impurity evaluation of set of values

    Returns the probability [0, 1], that the wrong category/prediction has been assigned.
    '''
    N = qs.count()
    counts = count_unique(qs, field)
    impurity = 0.0
    for k1 in counts:
        p1 = float(counts[k1]) / N
        for k2 in counts:
            if not k1 == k2:
                p2 = float(counts[k2]) / N
                impurity += p1 * p2
    return impurity


def entropy(qs, field, num_categories=2):
    """Total entropy for all the categorizations assigned

    sum(p(x) * log(p(x)) for x in count_unique(qs, field)

    Which measures how different each categorization is from the others
    """
    from math import log
    counts = count_unique(qs, field)
    ans = 0.0
    N = qs.count()
    for k in counts:
        p = float(counts[k]) / N
        if p:
            ans -=  p * log(p, num_categories)
    return ans


def entropy_and_impurity(qs, field, num_categories=2):
    """Gini impurity evaluation of predictions

    Returns the probability [0, 1], that the wrong category/prediction has been assigned.

    >>> entropy_and_impurity(tobes_data, -1)  # doctest: +ELLIPSIS
    (1.50524..., 0.6328125)
    """
    from math import log
    N = qs.count()
    counts = count_unique(qs, field)
    impurity = 0.0
    entropy = 0.0
    for k1 in counts:
        p1 = float(counts[k1]) / N
        if p1:
            entropy -= p1 * log(p1, num_categories)
        for k2 in counts:
            if not k1 == k2:
                p2 = float(counts[k2]) / N
                impurity += p1 * p2
    return entropy, impurity
# TODO: add class attributes `num_categories` and `field`
#       to allow configuration of fun for use in a map, lambda, etc


def impure_entropy(qs, field=-1):
    e, i = entropy_and_impurity(qs, field)
    return e * i


class DecisionNode:
    def __init__(self, col=-1, value=None, results=None, tb=None, fb=None):
        self.col=col
        self.value=value
        self.results=results
        self.tb=tb
        self.fb=fb


def build_tree(qs, field, scoref=entropy, ignore_fields=None, include_fields=None):
    """Build a classification decision tree

    >>> print_tree(build_tree(tobes_data))  # doctest: +NORMALIZE_WHITESPACE
    0:google? 
      T-> 3:21? 
          T-> {'Premium': 3}
          F-> 2:yes? 
              T-> {'Basic': 1}
              F-> {'None': 1}
      F-> 0:slashdot? 
          T-> {'None': 3}
          F-> 2:yes? 
              T-> {'Basic': 4}
              F-> 3:21? 
                  T-> {'Basic': 1}
                  F-> {'None': 3}
    """
    if ignore_fields is None:
        ignore_fields = ('pk', 'id')
    N = qs.count()
    if not N:
        return DecisionNode()
    if include_fields is None:
        include_fields = qs[0]._meta.get_all_field_names()

    current_score=scoref(qs, field)

    # Set up some variables to track the best criteria
    best_gain=0.0
    best_criteria=None
    best_sets=None

    for col in include_fields:
        if col in ignore_fields or col == field:
            continue
        # Set of unique values in this column
        # TODO: should do this once for all columns and cache it somewhere
        column_values = count_unique(qs, col)
        # Try dividing the table up for each value in this column
        for value in column_values:
            (set1, set2) = divide(qs, field=col, target=value, ignore_fields=ignore_fields, include_fields=include_fields)

            # Information improvement
            p = float(set1.count()) / N
            gain = current_score - p * scoref(set1, field) - (1 - p) * scoref(set2, field)
            if gain > best_gain and set1.count() > 0 and set2.count() > 0:
                best_gain = gain
                best_criteria = (col, value)
                best_sets = (set1, set2)

    # Create the sub branches   
    if best_gain > 0:
        trueBranch = build_tree(best_sets[0], field, ignore_fields=ignore_fields, include_fields=include_fields)
        falseBranch = build_tree(best_sets[1], field, ignore_fields=ignore_fields, include_fields=include_fields)
        return DecisionNode(col=best_criteria[0], value=best_criteria[1],
                            tb=trueBranch, fb=falseBranch)
    else:
        return DecisionNode(results=count_unique(qs, field=field)) 


def print_tree(tree, indent=' '):
    # if it's a leaf then results will be nonnull
    if tree.results is not None:
        print str(dict(tree.results))
    else:
        print str(tree.col) + ':' + str(tree.value) + '? '
        print indent + 'T->',
        print_tree(tree.tb,indent + '  ')
        print indent + 'F->',
        print_tree(tree.fb, indent + '  ')


def represent_tree(tree, indent=' '):
    s = ''
    # if it's a leaf then results will be nonnull
    if tree.results is not None:
        s += str(dict(tree.results)) + '\n'
    else:
        s += str(tree.col) + ':' + str(tree.value) + '?\n'
        s += indent + 'T->'
        s += represent_tree(tree.tb,indent + '  ') + '\n'
        s += indent + 'F->'
        s += represent_tree(tree.fb, indent + '  ') + '\n'
    return s


def get_width(tree):
    if tree.tb == None and tree.fb == None:
        return 1
    return get_width(tree.tb) + get_width(tree.fb)


def get_depth(tree):
    '''Walk a tree to get it's maximum depth (a nonnegative integer)'''
    if tree.tb == None and tree.fb == None:
        return 0
    if tree is None:
        return None
    return max(get_depth(tree.tb), get_depth(tree.fb)) + 1


def variance(qs, field):
    if len(qs) == 0:
        return 0
    column = qs.values(field)
    # FIXME: use ORM `Sum()` and `count()` and look for a Variance function (or create one?)
    data = [float(row[field]) for row in column]
    mean = sum(data) / len(data)
    variance = sum([(d - mean) ** 2 for d in data]) / len(data)
    return variance


def get(obj, key, default=None):
    '''Get a numbered element from a sequence or dict, or the attribute of an object'''
    if isinstance(obj, dict):
        if isinstance(key, int):
            try:
                return obj.get(sorted(tuple(obj))[key], default)
            except:
                pass
        try:
            return obj.get(key, default)
        except:
            pass
    try:
        # integer key and sequence (list) object
        return obj[key]
    except:
        return obj.getattr(key, default)

    





