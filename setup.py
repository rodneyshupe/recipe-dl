#!/usr/bin/env python

# Reference: https://packaging.python.org/tutorials/packaging-projects/

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

print (setuptools.find_packages())
exit(0)

setuptools.setup(

    name="recipe-dl-YOUR-USERNAME-HERE", # Replace with your own username
    name = 'recipe-dl',
    version="0.1.0",
    author = 'Rodney Shupe',
    author_email = 'rodney@shupe.ca',
    description = 'Recipe Downloader - Download Recipies from many websites and output as JSON, Markdown or reStructuredText.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url = 'https://github.com/rodneyshupe/recipe-dl.py',
    #packages = ['recipe-dl'],
    packages = setuptools.find_packages(),
    download_url = 'https://github.com/PolBaladas/torsimany/tarball/1.0',
    keywords = ['recipe', 'download', 'json', 'markdown', 'md', 'restructuredtext', 'rst', 'convert'],
    entry_points={
        'console_scripts': [
          'recipe-dl = recipe-dl.recipe-dl:main'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
