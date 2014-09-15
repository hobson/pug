% title: Data Science with `pug`
% subtitle: PDX-Python January 2014
% author: [Hobson Lane](http://github.com/hobsonlane)
% thankyou: Thanks PDX-Python!
% thankyou_details: And all these open source contributors:
% contact: [python](python.org)
% contact: [django](djangoproject.org)
% contact: [pyodbc](pypi.python.org/pypi/pyodbc)
% favicon: http://python.org/favicon.ico

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

<pre class="prettyprint" data-lang="shell">
    #/usr/bin/env python
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

    $ tail ~/.bash_history_forever
    # cd /home/Hobson
     7810  2014-01-17 17:42:22 workon dev
    # cd /home/Hobson/src/dev
     7811  2014-01-17 17:45:51 $ tail ~/.bash_history_forever

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

---


Here is a list that should build:

- I like formulas, like this one $e=mc^2$
- It's rendered using MathJax. You can change the settings by editing base.html if you like
- pressing 'f' toggle fullscreen
- pressing 'w' toggles widescreen
- 'o' toggles overview mode

---
title: Slide with a figure
subtitle: Subtitles are cool too
class: img-top-center

<img height=150 src=figures/200px-6n-graf.svg.png />

- Some point to make about about this figure from wikipedia
- This slide has a class that was defined in theme/css/custom.css

<footer class="source"> Always cite your sources! </footer>

---
title: Segue slide
subtitle: I can haz subtitlz?
class: segue dark nobackground

---
title: Maybe some code?

press 'h' to highlight an important section (that is highlighted
with &lt;b&gt;...&lt;/b&gt; tags)

<pre class="prettyprint" data-lang="javascript">
function isSmall() {
  return window.matchMedia("(min-device-width: ???)").matches;
}

<b>function hasTouch() {
  return Modernizr.touch;
}</b>

function detectFormFactor() {
  var device = DESKTOP;
  if (hasTouch()) {
    device = isSmall() ? PHONE : TABLET;
  }
  return device;
}
</pre>

