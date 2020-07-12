#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# # Clean the previous build package
# python setup.py clean --all
#
# # Create build package
# python setup.py sdist bdist_wheel
#
# # Install from local package
# pip3 install .
#

import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'recipe-dl',
    packages = find_packages(
        include=['recipe_dl', 'recipe_dl.*'],
        exclude=['*.rst', '*.txt', '*.md']
    ),
    #packages=['recipe_dl', 'recipe_dl.iso8601', 'recipe_dl.CustomPrint', 'recipe_dl.CustomExceptions'],
    version = '0.1.0',
    license = "GNU General Public License v3.0",
    description = 'Recipe Downloader - Download Recipies from many websites and output as JSON, Markdown or reStructuredText.',
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    author = 'Rodney Shupe',
    author_email = 'rodney@shupe.ca',
    url = 'https://github.com/rodneyshupe/recipe-dl',
    download_url = 'https://github.com/rodneyshupe/recipe-dl/tarball/1.0',
    keywords = ['recipe', 'download', 'json', 'markdown', 'md', 'restructuredtext', 'rst', 'convert'],
    entry_points={
        'console_scripts': [
            'recipe-dl=recipe_dl.recipe_dl:main'
        ]
    },
    classifiers = [
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
