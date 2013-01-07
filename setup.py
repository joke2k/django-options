from setuptools import setup, find_packages

VERSION = (1, 0, 0)

# Dynamically calculate the version based on VERSION tuple
if len(VERSION)>2 and VERSION[2] is not None:
    str_version = "%d.%d_%s" % VERSION[:3]
else:
    str_version = "%d.%d" % VERSION[:2]

version= str_version


setup(
    name='django-options',
    version=version ,
    author='joke2k',
    author_email='joke2k@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    url='http://github.com/joke2k/django-options',
    license='MIT',
    description='A easy way to manage Site options in your django applications.',
    classifiers=[
        # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Framework :: Django'
    ],
    keywords='faker fixtures data test django',
    install_requires=['django',],
    tests_require=['django','fake-factory>=0.2'],
    test_suite="runtests.runtests",
    zip_safe=False,
)