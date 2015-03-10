#!/usr/bin/env python
import os
import sys


if __name__ == "__main__":
    # print(os.environ.get('PYTHONPATH'))
    # os.environ['PYTHONPATH'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..')
    # print(os.environ['PYTHONPATH'])

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crawlnmine.settings.prod")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)