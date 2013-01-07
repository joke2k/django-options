"""

Django-options provides a global way to access to a dictionary of options
grouped by contrib.Site.

"""

__version__ = '0.1'

try:
    from .api import *
except ImportError:
    pass