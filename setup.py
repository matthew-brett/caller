#!/usr/bin/env python
''' Installation script for caller package '''

from distutils.core import setup

setup(name='caller',
      version='0.1a',
      description='Draft command line caller',
      author='Matthew Brett',
      author_email='matthew.brett@gmail.com',
      url='None',
      packages=['caller', 'caller.tests', 'biocaller'],
      )
