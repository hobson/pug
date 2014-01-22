#!/usr/bin/env python
# just a template for a function to edit models.py files
# modeled after the scrapy-ws.py command line tool

from __future__ import print_function

import optparse
import sys

import django
import pug.nlp.db


def get_commands():
    return {
        'help': help,
        'app': app,  # getattr(self, 'app') ?
        'use': use,
        'clean': clean,
    }


def app(args, opts):
    """app - list labels (names) of available django apps"""
    pass


def use(args, opts):
    """use - list databases aliases of available connections"""
    pass


def clean(args, opts):
    """clean - clean up the specified app's models.py file"""
    opts = opts or (lambda : 0)
    app = pug.nlp.db.get_app(args[0] or getattr(opts, 'app', None) or nlp.db.get_app()[0])
    model_names = args[1:] or getattr(opts, 'model_names', None) or django.db.models.get_models(app)
    for model_name in model_names:
        print(repr(model_name))
    
    pug.nlp.db.get_models(app)


def help(args, opts):
    """help - list available commands"""
    print("Available commands:")
    for _, func in sorted(get_commands().items()):
        print("  ", func.__doc__)


def parse_opts():
    usage = "%prog [options] <command> [arg] ..."
    description = "Django models.py cleaner. Use '%prog help' to see the list of available commands."
    op = optparse.OptionParser(usage=usage, description=description)
    op.add_option("-a", dest="app", default="", \
        help="App whos models need cleaning")
    op.add_option("-u", dest="port", type="int", default=6080, \
        help="Database alias that should be used to connect to the data.")
    opts, args = op.parse_args()
    if not args:
        op.print_help()
        sys.exit(2)
    cmdname, cmdargs, opts = args[0], args[1:], opts
    commands = get_commands()
    if cmdname not in commands:
        sys.stderr.write("Unknown command: %s\n\n" % cmdname)
        help(None, None)
        sys.exit(1)
    return commands[cmdname], cmdargs, opts


def main():
    cmd, args, opts = parse_opts()
    try:
        cmd(args, opts)
    except IndexError:
        print(cmd.__doc__)


if __name__ == '__main__':
    main()