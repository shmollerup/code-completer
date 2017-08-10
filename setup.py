#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-
from setuptools import setup, find_packages

## See the following pages for keywords possibilities for setup keywords, etc.
# https://packaging.python.org/
# https://docs.python.org/3/distutils/apiref.html
# https://docs.python.org/3/distutils/setupscript.html

setup(name='code-completer',
      version='0.2',
      package_dir={'': 'src'},
      packages=find_packages(where='src'),
      description='code completion tool implemented with neural net training',
      test_suite='code_completer.tests',
      provides=['code_completer'],
      maintainer="shm",
      maintainer_email="mollerup.2017@gmail.com",
      zip_safe=False)
