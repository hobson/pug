# `pug`
[![Build Status](https://travis-ci.org/hobson/pug.svg?branch=master "Travis Build & Test Status")](https://travis-ci.org/hobson/pug)
[![Coverage Status](https://coveralls.io/repos/hobson/pug/badge.png)](https://coveralls.io/r/hobson/pug)
[![Version Status](https://pypip.in/v/pug/badge.png)](https://pypi.python.org/pypi/pug/)
[![Downloads](https://pypip.in/d/pug/badge.png)](https://pypi.python.org/pypi/pug/)
[![License](https://pypip.in/license/pug/badge.svg?style=flat](https://github.com/hobson/pug/)

## Python User Group utilities

Collection of utilities by and for the PDX Python User Group.

- nlp    -- Natural Language (and text) Processing utilities
- ann    -- Artificial Neural Network utilities
- invest -- Time Series Processing utilities (including predictive analytics on financial time series)
- dj     -- Django utilities and apps (not yet working)


See [the docs](https://github.com/hobsonlane/pug/tree/master/docs "incomplete documentation") for the latest.

---

## Installation

### On a Posix System

You really want to contribute, right?

    git clone https://github.com/hobson/pug.git

If you're a user and not a developer, and have an up-to-date posix OS with the postgres, xml2, and xlst development packages installed, then just use `pip`.

    pip install pug

### Fedora

If you're on Fedora >= 16 but haven't done a lot of python binding development, then you'll need some libraries before pip will succeed.

    sudo yum install -y python-devel libxml2-devel libxslt-devel gcc-gfortran python-scikit-learn postgresql postgresql-server postgresql-libs postgresql-devel
    pip install pug

### Bleeding Edge

Even the releases are very unstable, but if you want to have the latest, most broken code

    pip install git+git://github.com/hobsonlane/pug.git@master

### Warning

This software is in alpha testing.  Install at your own risk.

---

## Development

I love merging PRs and adding contributors to the `__authors__` list:

    git clone https://github.com/hobson/pug.git
