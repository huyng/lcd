#!/usr/bin/env python
from distutils.core import setup

setup( name='lcd',
       version='0.1',
       description='Verified data structures for busy people',
       author='Huy Nguyen',
       author_email='huy@huyng.com',
       packages=['lcd'],
   )
       

# to distribute run:
# python setup.py register sdist bdist_wininst upload        