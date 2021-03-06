#!/usr/bin/env python
#
#   Copyright (c) 2011,2012,2013 Canonical Ltd.
#
#   This file is part of: SST (selenium-simple-test)
#   https://launchpad.net/selenium-simple-test
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#


import os
from setuptools import setup
import sys


this_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(this_dir, 'src'))

from sst import __version__


NAME = 'sst'
PACKAGES = ['sst', 'sst.scripts', 'sst.tests', 'sst.testrail_api']
DESCRIPTION = 'SST - Web and Native App Test Framework'
URL = 'http://testutils.org/sst'
LICENSE = 'Apache'

readme = os.path.join(this_dir, 'README')
LONG_DESCRIPTION = '\n%s' % open(readme).read()

requirements_file = os.path.join(this_dir, 'requirements.txt')
requirements = filter(None, open(requirements_file).read().splitlines())
REQUIREMENTS = [req for req in requirements if 'git+git' not in req]
REQUIREMENTS.append('sauceclient==1.0.1')

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Environment :: Web Environment',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache Software License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Operating System :: OS Independent',
    'Topic :: Software Development :: Libraries',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Software Development :: Testing',
    'Topic :: Software Development :: Quality Assurance',
    'Topic :: Internet :: WWW/HTTP :: Browsers',
]

AUTHOR = 'Canonical Online Services Team'
MAINTAINER = 'Warner Bros. Digital Labs'
MAINTAINER_EMAIL = 'qa@wbdl.com'
KEYWORDS = ('selenium appium webdriver test testing web automation').split(' ')

params = dict(
    name=NAME,
    version=__version__,
    packages=PACKAGES,
    package_dir={'': 'src', },
    package_data={'browsermob-proxy-2.1.2': ['browsermob-proxy-2.1.2/*']},
    include_package_data=True,
    install_requires=REQUIREMENTS,
    dependency_links=['git+https://github.com/cgoldberg/sauceclient@aa27b7d#egg=sauceclient-1.0.1'],

    # metadata for upload to PyPI
    author=AUTHOR,
    maintainer=MAINTAINER,
    maintainer_email=MAINTAINER_EMAIL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    keywords=KEYWORDS,
    url=URL,
    classifiers=CLASSIFIERS,

    entry_points={
        'console_scripts': [
            'sst-run = sst.scripts.run:main',
            'sst-remote = sst.scripts.remote:main',
            'sst-test = sst.scripts.test:main',
        ],
    },
)

setup(**params)
