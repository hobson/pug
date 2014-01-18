# Python User Group talk on Data Science

---

# Tips

1. Do things manually the first time
    
  a. Remind yourself, "This is productive EDA" not repetitive, mind-numbing Microsoft wrestling

  b. You'll know your data and databases better when your done

  c. You may discover things you didn't expect

2. Dump scripts from ipython history command before exiting each session

    #/usr/bin/env python
    #~/src/pug/bin/save_hist
    ip = get_ipython()
    this_line = list(ip.history_manager.get_tail())[-1][1]
    ip.magic(u'save -r test.py 0-%d' % this_line - 1)
    ip.exit

---

Dump bash commands using `history` or 

---

# Modules/Files

* nlp.db -- interracting with databases and migrating data
* nlp.util -- format numbers & dates, importing of "pivots" in spreadsheets
* nlp.strutil -- reformatting of strings