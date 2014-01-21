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

## Files

* bin -- command-line tools, .bashrc, and other config files
* nlp/db -- interracting with databases and migrating data
* nlp/util -- format numbers & dates, importing of "pivots" in spreadsheets
* nlp/strutil -- reformatting of strings

---


