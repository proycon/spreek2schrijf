#! /usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import print_function

import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "Spreek2Schrijf",
    version = "0.1",
    author = "Maarten van Gompel",
    author_email = "proycon@anaproy.nl",
    description = ("Scripts"),
    license = "GPL",
    keywords = "nlp computational_linguistics",
    url = "https://github.com/proycon/spreek2schrijf",
    packages=['spreek2schrijf'],
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Text Processing :: Linguistic",
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    zip_safe=False,
    include_package_data=True,
    package_data = { },
    install_requires=[  'python-ucto >= 0.2.2','python-Levenshtein','numpy','lxml'],
    entry_points = {    'console_scripts': [
        's2s-aligner = spreek2schrijf.aligner:main',
        's2s-buildparcorpus = spreek2schrijf.buildparcorpus:main',
        's2s-extracttext = spreek2schrijf.extracttext:main'
       ] }
)
