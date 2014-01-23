# System-wide .bashrc file for interactive bash(1) shells.

# To enable the settings / commands in this file for login shells as well,
# this file has to be sourced in /etc/profile.

# ~/.bashrc: executed by bash(1) for non-login shells.
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
# for examples

# If not running interactively, don't do anything
[ -z "$PS1" ] && return
echo "A customized /etc/bash.bashrc script is modifying your environment. It was launched with '$0' ......."

# Don't put duplicate lines in the history. See bash(1) for more options
# HISTCONTROL=${HISTCONTROL}+ignoredups
# ignoredups (don't record multiple repetitions of the same command) and ignorespace (don't record history for commands preceded by whitespace)
HISTCONTROL=ignoreboth
# don't overwrite GNU Midnight Commander's setting of `ignorespace'.
# HL: allow 1,000,000 history lines (including timestamp comment lines, etc)
HISTTIMEFORMAT="%Y-%m-%d %H:%M:%S " # trailing space makes history log look nicer
# allow 100K lines
HISTFILESIZE=1000000
HISTSIZE=HISTFILESIZE
# WARNING: don't forget to put the HISTSIZE lines above in both user and /etc/bash.bashrc files,
#  otherwise a cron-launched shell will truncate your history file
#  append the history file after each session
#  allow failed command substittution to be re-edited
#  command substitions are first presented to user before execution
shopt -s histappend histreedit histverify
# for setting history length see HISTSIZE and HISTFILESIZE in bash(1)

# prevent users from modifying these variables
readonly HISTFILESIZE
readonly HISTSIZE
readonly HISTCONTROL
readonly HISTIGNORE
readonly HISTTIMEFORMAT


#readonly PROMPT_COMMAND

# more history securing suggestions: 
#   sudo chown root:user ~/.bash_history_audit
#   sudo chmod 620 ~/.bash_history_audit
#   chattr +a ~/.bash_history_audit


#########################################################
# Bash shell options

# In an interactive terminal, execute a directory name as if you'd preceded it with "cd "
# shopt -s autocd

# These options can be dangerous in a script that cd's to a directory and then does something destructive, e.g., rm -rf *
# directory mispellings in a cd command are automatically corrected
#shopt -s cdspell
# if the string after a cd command is not a valid directory, 
# then assume it's a variable name and try to cd to the directory indicated in the variable
#shopt -s cdable_vars

# source command uses $PATH to search for scripts (set by default already)
shopt -s sourcepath

# command completion won't search $PATH for an empty command pattern
shopt -s no_empty_cmd_completion

# multiline commands are stored in a single history entry
shopt -s cmdhist

# (...) = (pattern1|pattern2|...)
# enables glob syntax like: ?(...) = 0/1, *(...) = >=0, +(...) = >=1, @(...) = OR, !(...) = NOT-OR
shopt -s extglob        # Necessary for programmable completion.

# apache style **/ and ** syntax in glob patterns
shopt -s globstar

# indexes all executable commands on the path with a hashtable and checks it before doing a full path search for a command
shopt -s checkhash

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize
#########################################################


#######################################################
# PATHs
# shell variable listing paths to append to PATH
MOREUSERPATHS=("." "/usr/share/fslint/fslint" "${HOME}/bin" "${HOME}/bin/python-scripts" "/usr/local/bin/")
for p in ${MOREUSERPATHS[*]}; do # Interestingly indexing with [*] or [@] seem to do the same thing.
  mkdir -p "$p"
  if [ -d ${p} ]; then
    echo "Adding to PATH -- $p"
    export PATH="${p}:${PATH}"
  else
    echo "INFO: Unable to find path '$p', so it wasn't added to your env \$PATH"
  fi
done

#######################################################


#########################################################
# GNU Plot Stuff
#export GDFONTPATH="/usr/share/fonts/truetype/ttf-bitstream-vera"
#export GNUPLOT_DEFAULT_GDFONT="Vera.ttf"
export GDFONTPATH="/usr/share/fonts/truetype/ttf-dejavu"
export GNUPLOT_DEFAULT_GDFONT="DejaVuSans.ttf"
#########################################################


#########################################################
# YII
if [ -d "${HOME}/src/yii-read-only/framework" ]; then
	export webroot="/var/www"
	export wwwroot="/var/www"
	export YIIFRAMEWORK="${HOME}/src/yii-read-only/framework"
	export YIIROOT="${HOME}/src/yii-read-only"
fi
#########################################################


#########################################################
# Python (virtualenvwrapper)
mkdir -p "$HOME/.virtualenvs"
export WORKON_HOME="$HOME/.virtualenvs"
mkdir -p "$HOME/src"
export PROJECT_HOME="$HOME/src"

if [ -f /usr/local/bin/virtualenvwrapper.sh ]; then
	source /usr/local/bin/virtualenvwrapper.sh
fi
if [ -f /usr/bin/virtualenvwrapper.sh ]; then
	source /usr/bin/virtualenvwrapper.sh
fi

#########################################################


#########################################
# KEEP KEYS PRIVATE!!!!
# import credentials, keys, passwords into users environment

if [ -f /etc/security/${USER}/.env.sh ]; then
    source /etc/security/${USER}/.env.sh
fi

#########################################


# Make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"


#########################################################
# Shell Prompt to record history and display active git branch, virtualenv, etc

# from stackoverflow to append pwd:
# export PROMPT_COMMAND='hpwd=$(history 1); hpwd="${hpwd# *[0-9]*  }"; if [[ ${hpwd%% *} == "cd" ]]; then cwd=$OLDPWD; else cwd=$PWD; fi; hpwd="${hpwd% ### *} ### $cwd"; history -s "$hpwd";'
# appends the pwd, but not the date, and my HISTTIMEFORMAT screws it up:
# export PROMPT_COMMAND='hpwd=$(history 1); hpwd="${hpwd# *[0-9]*  }"; if [[ ${hpwd%% *} == "cd" ]]; then cwd=$OLDPWD; else cwd=$PWD; fi; hpwd="${hpwd% ### *} ### $cwd"; history -s "$hpwd";'

# allow ctrl-S for history navigation (with ctrl-R)
# stty -ixon

# history -c # clears the current command history
# history -r # restores/retrieves the current history list from a file (default file is .bash_history?)
# export HISTSIZE=0 # stops saving history for this session
# unset HISTSIZE # stops saving history for this session
# history -w history-list.txt # export history to a file
# history -a history-list.txt # append the current history to an existing history file previously created with -w or -a
# history -r history-list.txt # retreive commands from a file and place in your current history list

# could probably also record the pwd (cwd) using the variable that is storing the directories for back and pushd and popd or $PWD
#echo "Prompt command: '${PROMPT_COMMAND}'" # /etc/bash.bashrc already contains a prompt command that saves/syncs history
touch /var/log/.bash_history_forever
export PROMPT_COMMAND="history -a; history -c; history -r; history 1 >> /var/log/.bash_history_forever; $PROMPT_COMMAND"
export PROMPT_COMMAND='echo "# cd $PWD" >> /var/log/.bash_history_forever; '$PROMPT_COMMAND
readonly PROMPT_COMMAND

function parse_git_branch {
	if [ -x /usr/bin/git ]; then
 		git branch --no-color 2> /dev/null | sed -e '/^[^*]/d' -e 's/*\(.*\)/\1/'
 	fi
}

function parse_hg_branch {
	if [ -x /usr/bin/git ]; then
		hg branch 2> /dev/null | sed -e 's/\(.*\)/\ hg\ \1/'
	fi
}

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color) color_prompt=yes;;
esac

# uncomment for a colored prompt, if the terminal has the capability; turned
# off by default to not distract the user: the focus in a terminal window
# should be on the output of commands, not on the prompt
force_color_prompt=yes

# set a fancy prompt (non-color, overwrite the one in /etc/profile)
PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '

PS1="$PS1\[\033[00;32m\]\$(parse_git_branch)\[\033[00m\]
\$ "
#######################################################


#######################################################
# Aliases

# Colorize ls and grep
if [ -x /usr/bin/dircolors ]; then
    test -r ${HOME}/.dircolors && eval "$(dircolors -b ${HOME}/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
    # alias pgrep='grep --color=auto --perl-regexp'
    alias fgrep='fgrep --color=auto --fixed-strings'
    alias egrep='egrep --color=auto --extended-regexp'
fi

#######################################################



# Commented out, don't overwrite xterm -T "title" -n "icontitle" by default.
# If this is an xterm set the title to user@host:dir
#case "$TERM" in
#xterm*|rxvt*)
#    PROMPT_COMMAND='echo -ne "\033]0;${USER}@${HOSTNAME}: ${PWD}\007"'
#    ;;
#*)
#    ;;
#esac


if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
	# We have color support; assume it's compliant with Ecma-48
	# (ISO/IEC-6429). (Lack of such support is extremely rare, and such
	# a case would tend to support setf rather than setaf.)
		color_prompt=yes
    else
		color_prompt=
    fi
fi


# enable bash completion in interactive shells
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi


# sudo hint
if [ ! -e "$HOME/.sudo_as_admin_successful" ] && [ ! -e "$HOME/.hushlogin" ] ; then
    case " $(groups) " in *\ admin\ *)
    if [ -x /usr/bin/sudo ]; then
	cat <<-EOF
	To run a command as administrator (user "root"), use "sudo <command>".
	See "man sudo_root" for details.
	
	EOF
    fi
    esac
fi


# if the command-not-found package is installed, use it
if [ -x /usr/lib/command-not-found -o -x /usr/share/command-not-found/command-not-found ]; then
	function command_not_found_handle {
	        # check because c-n-f could've been removed in the meantime
                if [ -x /usr/lib/command-not-found ]; then
		   /usr/lib/command-not-found -- "$1"
                   return $?
                elif [ -x /usr/share/command-not-found/command-not-found ]; then
		   /usr/share/command-not-found/command-not-found -- "$1"
                   return $?
		else
		   printf "%s: command not found\n" "$1" >&2
		   return 127
		fi
	}
fi
