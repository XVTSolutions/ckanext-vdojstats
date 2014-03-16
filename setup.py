from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(
    name='ckanext-vdojstats',
    version=version,
    description="statistics",
    long_description='''
    ''',
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='',
    author_email='',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.vdojstats'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points='''
        [ckan.plugins]
        # Add plugins here, e.g.
        vdojstats=ckanext.vdojstats.plugin:VDojStatsPlugin
    ''',
)
