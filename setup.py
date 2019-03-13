#!/usr/bin/env python

from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name             = 'speval',
    version          = '0.1.1',
    author           = 'Dmitrii Torbunov',
    author_email     = 'torbu001@umn.edu',
    url              = 'https://github.com/usert5432/speval',
    packages         = [ 'speval' ],
    description      = 'Simple Parellel Function Evaluator',
    long_description = readme(),
    license          = 'MIT',
)
