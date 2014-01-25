from pug.crawler.models import WikiItem
from pug.nlp.db_decision_tree import build_tree, print_tree, represent_tree
from pug.nlp.draw_tree import draw_tree
import pickle

tree_list = []
fields = ['dispatch_status']
qs_kwargs_list = [
        # quick test (small portion of database)
        {'id__gt':0, 'id__lt': 1000},
    ]
# each row is a different tree in the forest
include_fields_list = [
    ['wikiitem__modified', 'wikiitem__title'],
    ['wikiitem__modified', 'wikiitem__title'],
    ]

for i, field in enumerate(fields):
    for j, qs_kwargs in enumerate(qs_kwargs_list):
        for k, include_fields in enumerate(include_fields_list):
            print
            print '=' * 80
            print "Attempt to predict: %s" % field
            print "Limit database to: %s" % qs_kwargs
            print "Indicator variables: %s" % include_fields
            qs = WikiItem.objects.filter(**qs_kwargs)
            print "Fitting to %s records." % qs.count()
            print '-' * 80
            tree = build_tree(qs, field=field, include_fields=include_fields + [field])
            tree_list += [tree]
            print_tree(tree)
            print '-' * 80
            draw_tree(tree, 'tree_%s_%s_%s.jpg' % (i, j, k))
            with open('tree_%s_%s_%s.pickle' % (i, j, k), 'wb') as fpout:
                pickle.dump(tree, fpout)
            with open('tree_%s_%s_%s.txt' % (i, j, k), 'wb') as fpout:
                fpout.write(represent_tree(tree))
