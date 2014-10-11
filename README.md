# `pug`

## PDX-Python User Group utilities

---

![Codeship Status](https://www.codeship.io/projects/8df30150-32b4-0132-b8db-469abd0fd26c/status)

---

## Introduction

Collection of utilities by and for the PDX Python User Group.

- nlp -- natural language processing
- db -- database importing, etc
- dj -- some Django management commands
- wikiscrapy -- wikipedia crawler using [Scrapy](https://github.com/scrapy/scrapy "Excellent new crawler with a JSON-RPC API")
- docs -- some tips, examples, and yes, documentation

See [the docs](https://github.com/hobsonlane/pug/tree/master/pug/docs "incomplete documentation") for the latest.

---

## Installation

### On a Posix System

You really want to contribute, right?

    git clone

If your a user and not a developer, and have an up-to-date posix OS with the postgres, xml2, and xlst development packages installed, then use `pip`.

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

Help me, please:

    git clone git@github.com:hobsonlane/pug.git

I'll rubber stamp your pull requests on github within a day.
