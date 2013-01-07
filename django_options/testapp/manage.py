#!/usr/bin/env python
import os
import sys

DIRNAME = os.path.dirname(__file__)

if not DIRNAME in sys.path:
    sys.path.append(DIRNAME)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
