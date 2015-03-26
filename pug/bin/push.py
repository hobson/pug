#!/usr/bin/env python
from __future__ import print_function
# import future

import datetime
import argparse
import sys

import gitapi

def main():
    parser = argparse.ArgumentParser()

    #-db DATABASE -u USERNAME -p PASSWORD -size 20000
    parser.add_argument("positional_message", metavar="message", default="", nargs="?",
        help="Commit message (same message used for all repositories)")
    parser.add_argument("-m", "--message",  dest="message",  default="", 
        help="Commit message (same message used for all repositories)")
    parser.add_argument("-b", "--bumpsize", dest="bumpsize", default=0, type=int,
        help="Version level to incrment, default = 0.  0: leave version unchanged;  1: increment micro version;  2: increment minor version; 3 : increment major versionize")

    args = parser.parse_args()

    # use bash array to do this right or do it in python

    print("First arg to push.py = {}".format(args.positional_message))
    msg = "Automatic pug commit (along with subpackages) using script '{}' (usually pug/bin/push.py) on {} at {}.".format(
        __file__, datetime.date.today().strftime('%Y-%m-%d'),  datetime.datetime.now().strftime(r'%H:%M:%S %TZ'))
    if args.positional_message or args.message:
        msg = (args.positional_message or args.message) + '\n\n' + msg
    print("Commit message = {}".format(msg))

    repo = gitapi.Repo('.')
    refspec = repo.git_id()

    print("pug git repo = {}".format(repo))
    print("pug git refspec = {}".format(refspec))

    # cd $HOME/src/pug/
    # git commit -am "$COMMIT_MSG"
    # git pull
    # git push

    # cd $HOME/src/pug-nlp/
    # git commit -am "$COMMIT_MSG"
    # git pull
    # git push

    # cd $HOME/src/pug-dj/
    # git commit -am "$COMMIT_MSG"
    # git pull
    # git push

    # cd $HOME/src/pug-ann/
    # git commit -am "$COMMIT_MSG"
    # git pull
    # git push

    # cd $HOME/src/pug-invest/
    # git commit -am "$COMMIT_MSG"
    # git pull
    # git push
    return 0

if __name__ == '__main__':
    sys.exit(main())