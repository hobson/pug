#!/usr/bin/env bash

# use bash array to do this right or do it in python

cd ~/src/pug/
git commit -am "$1"
git pull
git push

cd ~/src/pug-nlp/
git commit -am "$1"
git pull
git push

cd ~/src/pug-dj/
git commit -am "$1"
git pull
git push

cd ~/src/pug-ann/
git commit -am "$1"
git pull
git push

cd ~/src/pug-invest/
git commit -am "$1"
git pull
git push
