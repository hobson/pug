#!/usr/bin/env bash

# use bash array to do this right or do it in python

echo "First arg to push.sh = $1"



PROJECT_NAME="Automatic pug (and subpackage) commit with command '${0}' (usually pug/bin/push.sh) at $(date)"
if [ -n "${1}" ]; then
    PROJECT_NAME="${1}"
fi
echo "Project Name    = $PROJECT_NAME"

PROJECT_VER="Automatic pug (and subpackage) commit with command '${0}' (usually pug/bin/push.sh) at $(date)"
if [ -n "${2}" ]; then
    PROJECT_VER="${2}"
fi
echo "Project Version = $PROJECT_VER"

COMMIT_MSG="Automatic pug (and subpackage) commit with command '${0}' (usually pug/bin/push.sh) at $(date)"
if [ -n "${3}" ]; then
    COMMIT_MSG="${3}"
fi
echo "Commit Message  = $COMMIT_MSG"

cd $HOME/src/pug-$PROJECT_NAME/
pandoc README.md -o README.rst
git commit -am "$COMMIT_MSG"
git pull
git push
python "pug/${PROJECT_NAME}/tests.py" && python setup.py register -r pypitest && python setup.py sdist upload -r pypitest && git tag "${PROJECT_VER}" && git push --tag && python setup.py register -r pypi && python setup.py sdist upload -r pypi

