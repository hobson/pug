#test_decider.py


from call_center.models import CaseExchange, CaseHDTVHeader, CaseMaster

from pug.db.explore import count_unique
from pug.nlp.db_decision_tree import build_tree, print_tree


N = CaseMaster.objects.count()
UN = CaseMaster.objects.values('case_number').distinct().count()
N_ce = CaseExchange.objects.count()
UN_ce = CaseExchange.objects.values('case_number').distinct().count()
N_hdtv = CaseHDTVHeader.objects.count()
UN_hdtv = CaseHDTVHeader.objects.values('case_number').distinct().count()


un = count_unique(CaseExchange.objects.values('case_number'), 'case_number')
assert(len(un.values()) == UN_ce)
assert(sum(un.values()) == N_ce)


qs = CaseHDTVHeader.objects.filter(case_number__lt=4000000)
ex = qs.all()[0]
ex.service_calls
print_tree(build_tree(qs, field='service_calls', ignore_fields=('id', 'case_number')))
# dispatch_status:Completed ? 
#  T-> date_time:2008-09-15 12:25:34.270000? 
#    T-> {1: 1}
#    F-> date_time:2008-07-09 08:49:36.437000? 
#      T-> {0: 1}
#      F-> {None: 0}
#  F-> {None: 0}
qs = CaseHDTVHeader.objects.filter(case_number__lt=2000000)
ex = qs.all()[0]
ex.service_calls
print_tree(build_tree(qs, field='dispatch_status', ignore_fields=('id', 'case_number', 'service_calls')))
# dispatch_status:Completed ? 
#  T-> date_time:2008-09-15 12:25:34.270000? 
#    T-> {1: 1}
#    F-> date_time:2008-07-09 08:49:36.437000? 
#      T-> {0: 1}
#      F-> {None: 0}
#  F-> {None: 0}

print_tree(build_tree(qs, field='dispatch_status', ignore_fields=('id', 'dispatch_rejected', 'case_number', 'service_calls', 'dispatch_reject_reason', 'dispatch_reject_reason', 'dispatch_create', 'dispatch_completed', 'dispatch_expired', 'dispatch_scheduled', 'dispatch_received')))
print_tree(build_tree(qs, field='dispatch_status', include_fields=('user_type', 'purchase_where', 'repair_exch', 'case_number__state', 'case_number__model', 'case_number__contact_method')))
print_tree(build_tree(qs, field='service_calls', ignore_fields=('id', 'case_number')))
# s_state:TX? 
#  T-> servicer_refno:4656388                  ? 
#    T-> date_time:2003-02-06 17:27:25.390000? 
#      T-> {3: 1}
#      F-> {2: 1}
#    F-> case_number:797996? 
#      T-> {None: 0}
#      F-> {1: 3}
#  F-> store_name:Cardinal TV and Audio              ? 
#    T-> date_time:2002-04-08 14:35:25.900000? 
#      T-> {2: 1}
#      F-> {1: 1}
#    F-> {None: 0}

query_set = CaseHDTVHeader.objects.filter(case_number__gt=3000000, case_number__lt=3500000)
tree = build_tree(query_set, field='dispatch_status', include_fields=(
    'user_type',
    'dispatch_status',
    'case_number__state',
    'case_number__model',
    'case_number__country',
    'case_number__zip',
    'case_number__queue_time',
    'case_number__problem',
    'case_number__call_type',
    'case_number__contact_method'))
print_tree(tree)

#print_tree(tree)

# case_number__queue_time:2008-01-29 10:44:12.537000? 
#  T-> case_number__queue_time:2008-01-29 12:01:47.393000? 
#    T-> case_number__queue_time:2009-03-23 15:21:10.390000? 
#      T-> case_number__problem:7E11? 
#        T-> {None: 0}
#        F-> case_number__problem:7D00? 
#          T-> case_number__state:TN? 
#            T-> {u'Completed ': 1, None: 0}
#            F-> {None: 0}
#          F-> case_number__model:LC42D62U         ? 
#            T-> {None: 0}
#            F-> case_number__state:NJ? 
#              T-> {u'Accepted  ': 1}
#              F-> case_number__state:OH? 
#                T-> {u'Accepted  ': 1}
#                F-> case_number__state:CA? 
#                  T-> {u'Accepted  ': 1}
#                  F-> case_number__state:HI? 
#                    T-> {None: 0}
#                    F-> case_number__model:KB6015KS         ? 
#                      T-> {None: 0}
#                      F-> user_type:None? 
#                        T-> {u'Completed ': 1}
#                        F-> case_number__state:MI? 
#                          T-> {u'Completed ': 1}
#                          F-> {u'Completed ': 2, None: 0}
#      F-> case_number__problem:7B00? 
#        T-> {u'Accepted  ': 1}
#        F-> case_number__model:LC52D82U         ? 
#          T-> {u'Completed ': 1}
#          F-> case_number__model:LC40C32U         ? 
#            T-> case_number__state:NY? 
#              T-> {u'Completed ': 1}
#              F-> {None: 0}
#            F-> case_number__contact_method:6? 
#              T-> {None: 0}
#              F-> case_number__problem:5011? 
#                T-> {u'Completed ': 1, None: 0}
#                F-> case_number__queue_time:2008-10-29 11:28:45.207000? 
#                  T-> case_number__queue_time:2008-10-29 18:47:01.450000? 
#                    T-> case_number__state:NY? 
#                      T-> {u'Completed ': 1, None: 0}
#                      F-> {None: 0}
#                    F-> {u'Completed ': 1}
#                  F-> {None: 0}
#    F-> {u'Cancelled ': 1, u'Accepted  ': 1}
#  F-> case_number__state:FL? 
#    T-> case_number__model:LC37D6U          ? 
#      T-> {u'Completed ': 1}
#      F-> case_number__model:LC26D4U          ? 
#        T-> {u'Completed ': 1}
#        F-> {None: 0}
#    F-> {None: 0}


from call_center.models import CaseHDTVHeader
from pug.nlp.db_decision_tree import build_tree, draw_tree, print_tree

tree_list = []
fields = ['dispatch_status']
qs_kwargs_list = [
    {'case_number__gt':3000000, 'case_number__lt': 3200000},
    {'case_number__gt':3200000, 'case_number__lt': 3600000},
    {'case_number__gt':3600000, 'case_number__lt': 4000000}
    ]
include_fields_list = [
    list('user_type', 'case_number__state', 'case_number__problem'),
    list('user_type', 'case_number__problem', 'case_number__model_number'),
    list('user_type', 'case_number__call_type', 'case_number__contact_method'),
    ]
for i, field in enumerate(fields):
    for j, qs_kwargs in enumerate(qs_kwargs_list):
        for k, include_fields in enumerate(include_fields_list):
            tree = [field, qs_kwargs, include_fields + field, build_tree(CaseHDTVHeader.objects.filter(**qs_kwargs), field=field, include_fields=include_fields)]
            tree_list += tree
            print
            print '=' * 80
            print field, qs_kwargs_list
            print include_fields
            print '-' * 80
            print_tree(tree)
            print '-' * 80
            draw_tree('tree_%s_%s_%s.jpg' % (i, j, k))