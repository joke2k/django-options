#!/usr/bin/env python
import sys

from django.conf import settings

def configure():

    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
                }
        },
        INSTALLED_APPS=(
            'django.contrib.sites',
            'django_faker',
            'django_options',
            'picklefield',
            'django_extensions',
            ),
        SITE_ID=1,
    )

if not settings.configured: configure()


def runtests(app_labels=None, verbosity=1):
    from django.test.utils import get_runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=verbosity, interactive=True, failfast=False)
    failures = test_runner.run_tests(app_labels or ['django_faker', 'picklefield', 'django_options'])
    sys.exit(failures)


if __name__ == '__main__':
    import sys
    verbosity = 1
    args = sys.argv[1:]
    idx = args.index('-v') if '-v' in args else -1
    if idx != -1:
        args.pop(idx)
        verbosity = int(args.pop(idx)) if len(args) > idx else 2

    runtests(args, verbosity=verbosity)


