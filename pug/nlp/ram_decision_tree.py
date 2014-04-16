# decision tree for list of lists (table) classification
# attempts to identify cases that result in a service call

from examples import tobes_data
from nlp.db.explore import count_unique


#from  django.db.models import Manager
#from django.db.models.query import QuerySet

def divide(table, field, target=0, default=0, return_type=list, ignore_fields=['id', 'pk']):
    judge = None
    # TODO: DRY this up! Could make judges a dict with (type, type) as keys. See git branch 'unlambda'

    # row is a dict (potentially a QuerySet.values() object)
    keys = None
    if hasattr(table[0], 'get'):
        # convert the integer index into a dict key
        if isinstance(field, int):
            # need to sort this list of keys to get a consistent order
            keys = sorted(tuple(k for k in table[0] if k not in ignore_fields))
            keyed_field = keys[field]
        else:
            keyed_field = field
        if isinstance(target, (int, float, bool)):
            judge = lambda row: row.get(keyed_field, default) >= target
        elif isinstance(target, (tuple, list, dict, set)):
            judge = lambda row: row.get(keyed_field, default) in target
        else:
            judge = lambda row: row.get(keyed_field, default) == target
    elif isinstance(table, (list, tuple)) or isinstance(field, (int, float)):
        if isinstance(target, (int, float, bool)):
            judge = lambda row: row[field] >= target
        elif isinstance(target, (tuple, list, dict, set)):
            judge = lambda row: row[field] in target
        else:
            judge = lambda row: row[field] == target
    else:
        if isinstance(target, (int, float, bool)):
            judge = lambda row: getattr(row, field, default) >= target
        elif isinstance(target, (tuple, list, dict, set)):
            judge = lambda row: getattr(row, field, default) in target
        else:
            judge = lambda row: getattr(row, field, default) == target

    # create an iterator/generator with yield or just annotate the row
    if keys:
        true_group = return_type(return_type(row[k] for k in keys) for row in table if judge(row))
        false_group = return_type(return_type(row[k] for k in keys) for row in table if not judge(row))
    else:
        true_group = return_type(row for row in table if judge(row))
        false_group = return_type(row for row in table if not judge(row))

    # import inspect
    # print inspect.getsource(judge)
    
    return (true_group, false_group)


def gini_impurity(table, field=-1):
    """Gini impurity evaluation of predictions

    Returns the probability [0, 1], that the wrong category/prediction has been assigned.
    """
    try:
        N = table.count()
    except:
        N = len(table)
    counts = count_unique(table, field)
    impurity = 0.0
    for k1 in counts:
        p1 = float(counts[k1]) / N
        for k2 in counts:
            if not k1 == k2:
                p2 = float(counts[k2]) / N
                impurity += p1 * p2
    return impurity


def entropy(table, field=-1, num_categories=2):
    """Total entropy for all the categorizations assigned

    sum(p(x) * log(p(x)) for x in count_unique(table, field)

    Which measures how different each categorization is from the others
    """
    from math import log
    counts = count_unique(table, field)
    entropy = 0.0
    try:
        N = table.count()
    except:
        N = len(table)
    for k in counts:
        p = float(counts[k]) / N
        entropy -=  p * log(p, num_categories)
    return entropy


def entropy_and_impurity(table, field=-1, num_categories=2):
    """Gini impurity evaluation of predictions

    Returns the probability [0, 1], that the wrong category/prediction has been assigned.

    >>> entropy_and_impurity(tobes_data, -1)  # doctest: +ELLIPSIS
    (1.50524..., 0.6328125)
    """
    from math import log
    try:
        N = table.count()
    except:
        N = len(table)
    counts = count_unique(table, field)
    impurity = 0.0
    entropy = 0.0
    for k1 in counts:
        p1 = float(counts[k1]) / N
        entropy -= p1 * log(p1, num_categories)
        for k2 in counts:
            if not k1 == k2:
                p2 = float(counts[k2]) / N
                impurity += p1 * p2
    return entropy, impurity
# TODO: add class attributes `num_categories` and `field`
#       to allow configuration of fun for use in a map, lambda, etc


def impure_entropy(table, field=-1):
    e, i = entropy_and_impurity(table, field)
    return e * i


# def build_tree(table, field, scorer=entropy):
#     if not table:
#         return decision_node()
#     score = scorer(table, field)

#     best_gain = 0.0
#     best_sets = None

#     column_values = {}
#     M = len(table[0])
#     for row in table:
#         for i in range(M):
#             column_values[get(row, i)] = 1
#     pass


class DecisionNode(object):
    def __init__(self, col=-1, value=None, results=None, tb=None, fb=None):
        self.col=col
        self.value=value
        self.results=results
        # FIXME: tb s/b true_branch
        self.tb=tb
        self.fb=fb


def build_tree(table, field=-1, scoref=entropy, ignore_fields=('pk', 'id')):
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
    try:
        N = len(table)
    except:
        try:
            N = table.count()
        except:
            N = 0

    if not N:
        return DecisionNode()


    current_score=scoref(table)

    # Set up some variables to track the best criteria
    best_gain=0.0
    best_criteria=None
    best_sets=None
    if isinstance(table[0], dict) and isinstance(field, int):
        keys = sorted(tuple(k for k in table[0] if k not in ignore_fields))
        M = len(keys)
    else:
        M = len(table[0])
        keys = range(M)
    keyed_field = keys[field]

    for col in range(M):
        keyed_col = keys[col]

        if keyed_col == keyed_field:
            continue
        # Generate the list of different values in
        # this column
        column_values = set()
        for row in table:
            column_values.add(get(row, keyed_col))
        # Try dividing the table up for each value in this column
        for value in column_values:
            (set1, set2) = divide(table, field=col, target=value)
            set1, set2 = tuple(set1), tuple(set2)
            
            # Information improvement
            p = float(len(set1)) / N
            gain = current_score - p * scoref(set1) - (1 - p) * scoref(set2)
            if gain > best_gain and len(set1) > 0 and len(set2) > 0:
                best_gain = gain
                best_criteria = (col, value)
                best_sets = (set1, set2)

    # Create the sub branches   
    if best_gain > 0:
        trueBranch = build_tree(best_sets[0])
        falseBranch = build_tree(best_sets[1])
        return DecisionNode(col=best_criteria[0], value=best_criteria[1],
                            tb=trueBranch, fb=falseBranch)
    else:
        return DecisionNode(results=count_unique(table, field=keyed_field))  #keyed_field


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

    





