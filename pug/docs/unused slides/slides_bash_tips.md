% title: Data Science with `pug`
% subtitle: PDX-Python January 2014
% author: <a href="https://github.com/hobsonlane">Hobson Lane</a>
% thankyou: Thanks PDX-Python!
% thankyou_details: And all these open source contributors...
% contact: <a href="http://djangoproject.org">Django</a>
% contact: <a href="http://python.org">Python</a>
% contact: <a href="http://pypi.python.org/pypi/pyodbc">pyODBC</a>
% favicon: <img src="https://www.python.org/favicon.ico"/>

---
title: Tips
build_lists: true

### General

1. sublime rules
2. linters make sublime more sublime

---

### Data
title: Tips
build_lists: true


1. Import or munge your data manually the first time
    
  a. Remind yourself, "This is productive EDA" not repetitive, mind-numbing, Microsoft-wrestling

  b. You'll know your data and databases better when your done

  c. You may discover things you didn't expect

---

### Data

2. Dump scripts from ipython history command before exiting each session

<pre class="prettyprint" data-lang="python">
    #~/src/pug/bin/save_hist
    ip = get_ipython()
    this_line = list(ip.history_manager.get_tail())[-1][1]
    ip.magic(u'save -r test.py 0-%d' % this_line - 1)
    ip.exit

---

Dump bash commands using `history` or keep a running log of where you were and what you did with a `.bashrc` script like:

<pre class="prettyprint" data-lang="shell">
    export USR_BIN=$(dirname $(which virtualenv))
    export PROMPT_COMMAND='echo "# cd $PWD" >> ~/.bash_history_forever;
      '$PROMPT_COMMAND
    export PROMPT_COMMAND="
      history -a; history -c; history -r;
      history 1 >> ~/.bash_history_forever; $PROMPT_COMMAND"
    readonly PROMPT_COMMAND

---

and you'll end up with a colorized prompt:

<pre class="prettyprint" data-lang="shell">
    Hobson@cstmatlablx01:~$ 
    $ workon dev
    (dev)Hobson@cstmatlablx01:~/src/dev$

---

and your every move will be recorded: 

<pre class="prettyprint" data-lang="bash">
    $ tail ~/.bash_history_forever
    # cd /home/Hobson
     7810  2014-01-17 17:42:22 workon dev
    # cd /home/Hobson/src/dev
     7811  2014-01-17 17:45:51 $ tail ~/.bash_history_forever
</pre>

---

If you like a lot of important info in your prompt (like the git branch you are on):

<pre class="prettyprint" data-lang="bash">
    if [ -n "$force_color_prompt" ]; then
        if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
        color_prompt=yes
        else
        color_prompt=
        fi
    fi

    if [ "$color_prompt" = yes ]; then
        PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
    else
        PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
    fi
    unset color_prompt force_color_prompt

    case "$TERM" in
    xterm*|rxvt*)
        PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
        ;;
    *)
        ;;
    esac

    PS1="$PS1\[\033[00;32m\]\$(parse_git_branch)\[\033[00m\]
    \$ "
</pre>

---

### Counting Word Occurrences

<pre class="prettyprint" data-lang="python">
    from pug.nlp.classifier import get_words
    from collections import Counter

    docs = ['Explicit is better than implicit.',
            'Simple is better than complex.',
            'Flat is better than nested.',
           ]
    O_sparse = [Counter(get_words(d)) for d in docs]
    print O_sparse
    total = Counter()
    for c in O_sparse:
        total += c
    print total
</pre>

### Occurrence Matrix

<pre class="prettyprint" data-lang="python">
    from tabulate import tabulate
    words, O = list(total), []
    for counts in O_sparse:
        O += [[0] * len(words)]
        for word, count in counts.iteritems():
            j = words.index(word)
            O[-1][j] += count
    print tabulate(O, words, "pipe")
</pre>


|   flat |   simple |   explicit |   than |   better |   complex |   nested |   implicit |
|-------:|---------:|-----------:|-------:|---------:|----------:|---------:|-----------:|
|      0 |        0 |          1 |      1 |        1 |         0 |        0 |          1 |
|      0 |        1 |          0 |      1 |        1 |         1 |        0 |          0 |
|      1 |        0 |          0 |      1 |        1 |         0 |        1 |          0 |

---

### Graph Visualization with D3

* Our word occurrence matrix shows connections
    - word1 <--0--> doc1
    - word2 <--3--> doc1
    - ...
* This is a directed graph
    - source: word
    - target: document
    - value: frequency (number of occurrences)


---

<a href>http://localhost:8001/occurrence_force_graph.html>Explore it</a>

* Notice the outlier, George Washington... because of infrequent use of "the"
* Difficult to untangle the mess
    - Additional pop ups and highlighting of edges would help
    - Additional dimensions as size/shape of circles
    - What about short-circuiting the documents to see word-word connections?

---


---
## Files

* bin -- command-line tools, .bashrc, and other config files
* nlp/db -- interracting with databases and migrating data
* nlp/util -- format numbers & dates, importing of "pivots" in spreadsheets
* nlp/strutil -- reformatting of strings

---


