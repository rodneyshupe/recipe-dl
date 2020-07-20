#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def required():
    with open('requirements.txt') as f:
        return_value = f.read().splitlines()

    return_value.append("CustomPrint @ git+ssh://git@github.com/rodneyshupe/CustomPrint@v1.0.0#egg=CustomPrint")
    return_value.append("iso8601 @ git+ssh://git@github.com/rodneyshupe/iso8601@v1.0.0#egg=iso8601")

    return return_value

setup(
    name = 'recipe-dl',
    packages = find_packages(
        include=['recipe_dl', 'recipe_dl.*'],
        exclude=['*.rst', '*.txt', '*.md']
    ),
    install_requires=required(),
    #dependency_links=['http://github.com/rodneyshupe/CustomPrint/tarball/master#egg=CustomPrint-0.0.3'],
    version = '0.2.4',
    license = "GNU General Public License v3.0",
    description = 'Recipe Downloader - Download Recipies from many websites and output as JSON, Markdown or reStructuredText.',
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    author = 'Rodney Shupe',
    author_email = 'rodney@shupe.ca',
    url = 'https://github.com/rodneyshupe/recipe-dl',
    keywords = ['recipe', 'download', 'json', 'markdown', 'md', 'restructuredtext', 'rst', 'convert'],
    entry_points={
        'console_scripts': [
            'recipe-dl=recipe_dl.main:main'
        ]
    },
    classifiers = [
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
