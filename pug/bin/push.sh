#!/usr/bin/env bash

# use bash array to do this right or do it in python

echo "First arg to push.sh = $1"

COMMIT_MSG="Automatic pug (and subpackage) commit with command '${0}' (usually pug/bin/push.sh) at $(date)"
if [ -n "${1}" ]; then
    COMMIT_MSG="${1}"
fi

echo "Commit Message = $COMMIT_MSG"

cd $HOME/src/pug/
pandoc README.md -o README.rst
git commit -am "$COMMIT_MSG"
git pull
git push

cd $HOME/src/pug-nlp/
pandoc README.md -o README.rst
git commit -am "$COMMIT_MSG"
git pull
git push

cd $HOME/src/pug-dj/
pandoc README.md -o README.rst
git commit -am "$COMMIT_MSG"
git pull
git push

cd $HOME/src/pug-ann/
pandoc README.md -o README.rst
git commit -am "$COMMIT_MSG"
git pull
git push

cd $HOME/src/pug-invest/
pandoc README.md -o README.rst
git commit -am "$COMMIT_MSG"
git pull
git push
