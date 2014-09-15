# Data Science with `pug`

## PDX-Python January 2014

### Hobson Lane

---

## Agenda

Toolbox 
Corporate DBA

---

## Data Science

* Typical process
    * Tools
        - iPython (including Notebook)
        - Django
        - Numpy
        - D3
    * Examples
* Corporate Challenges
    * Leeching data from Microsoft databases
    * Microsoft LANs and VPNs
    * Politics

---

* Traditional ETL Approach
    * Extract
        - Query databases, crawl web, poll APIs
    * Transform (migrate into a data model you know)
    * Load
        - fixtures into Django, baks into sqlserver
        - python scripts to pull from source db and push to working mirror

--- My Approach

* Mirror
    - Python scripts to look for new data and pull it into your working copy
* Explore
    - Get metadata
        + Number of tables, fields, records
        + Field types and ranges
        + Value frequencies, and uniqueness
        + Entropy, correlation coefficients
    - Visualize
        + Table relationship diagrams
        + Histograms
        + Scatter plots
* Model
    - Transform: Clean, normalize, smooth
    - Expand or Reduce Dimensions: word frequencies, ignore/combine fields, add/remove relationships
    - Predict: interpolate, extrapolate
Load (ins
EDA


## Tips

### General

1. sublime rules
2. linters make sublime more sublime

### Data

1. Import or munge your data manually the first time
    
  a. Remind yourself, "This is productive EDA" not repetitive, mind-numbing, Microsoft-wrestling

  b. You'll know your data and databases better when your done

  c. You may discover things you didn't expect

---

Data
----

Dump scripts from ipython history command before exiting each session

    #!/usr/bin/python
    ip = get_ipython()
    this_line = list(ip.history_manager.get_tail())[-1][1]
    ip.magic(u'save -r test.py 0-%d' % this_line - 1)
    ip.exit

---

Dump bash commands using `history` or keep a running log of where you were and what you did with a `.bashrc` script like:

    #!/usr/bin/env bash
    export USR_BIN=$(dirname $(which virtualenv))
    export PROMPT_COMMAND='echo "# cd $PWD" >> ~/.bash_history_forever;
      '$PROMPT_COMMAND
    export PROMPT_COMMAND="
      history -a; history -c; history -r;
      history 1 >> ~/.bash_history_forever; $PROMPT_COMMAND"
    readonly PROMPT_COMMAND

---

and you'll end up with a colorized prompt:

    Hobson@cstmatlablx01:~$ 
    $ workon dev
    (dev)Hobson@cstmatlablx01:~/src/dev$

---

and your every move will be recorded: 

    $ tail ~/.bash_history_forever
    # cd /home/Hobson
     7810  2014-01-17 17:42:22 workon dev
    # cd /home/Hobson/src/dev
     7811  2014-01-17 17:45:51 tail ~/.bash_history_forever

---

    If you like a lot of important info in your prompt (like the git branch you are on):

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

---

## Files

* bin -- command-line tools, .bashrc, and other config files
* nlp/db -- interracting with databases and migrating data
* nlp/util -- format numbers & dates, importing of "pivots" in spreadsheets
* nlp/strutil -- reformatting of strings