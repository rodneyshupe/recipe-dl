from setuptools import setup
setup(
  name = 'recipe-dl',
  packages = ['recipe-dl'],
  version = '1.0',
  description = 'Recipe Downloader - Download Recipies from many websites and output as JSON, Markdown or reStructuredText.',
  author = 'Rodney Shupe',
  author_email = 'rodney@shupe.ca',
  url = 'https://github.com/rodneyshupe/recipe-dl',
  download_url = 'https://github.com/rodneyshupe/recipe-dl/tarball/1.0',
  keywords = ['recipe', 'download', 'json', 'markdown', 'md', 'restructuredtext', 'rst', 'convert'],
  entry_points={
    'console_scripts': [
      'recipe-dl = recipe-dl.recipe-dl:main'
    ]
  },
  classifiers = ['Programming Language :: Python :: 3'],
)
