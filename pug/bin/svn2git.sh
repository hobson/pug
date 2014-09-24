#!/usr/bin/env bash
#svn2git.sh
#convert an SVN repository (identified with a remote svn URL) to a local, bar git repo

SVNURL="http://aima-python.googlecode.com/svn"
SVNURL="$1"

# check out a local copy of the remote SVN repo
rm -rf ~/.tmp-svn
svn checkout "$SVNURL" ~/.tmp-svn

# reformat the list of authors to a format git understands
cd ~/.tmp-svn
svn log -q | awk -F '|' '/^r/ {sub("^ ", "", $2); sub(" $", "", $2); print $2" = "$2" <"$2">"}' | sort -u > author-list-formatted-for-git.txt

# clone/checkout the SVN repo again, but this time using git-svn and the newly formated authors.txt
git svn clone "$SVNURL" --no-metadata -A author-list-formatted-for-git.txt --stdlayout ~/.tmp-git

# get all the ignore properties from SVN and append them to a .gitignore file
# FIXME: this fails with error code 1 for http://aima-python.googlecode.com/svn
cd ~/.tmp-git
git svn show-ignore >> .gitignore
git add .gitignore
git commit -m 'Convert svn:ignore to .gitignore.'

# create an empty and bare git repo
rm -rf ~/.tmp-bare.git
git init --bare ~/.tmp-bare.git
cd ~/.tmp-bare.git
git symbolic-ref HEAD refs/heads/trunk

# push the git-svn repo to the new bare git repo
cd ~/.tmp-git
git remote add bare ~/.tmp-bare.git
git config remote.bare.push 'refs/remotes/*:refs/heads/*'
git push bare

# rename the trunk branch "master"
cd ~/.tmp-bare.git
git branch -m trunk master

# convert svn tag names into real git tags
# FIXME: didn't do anything for http://aima-python.googlecode.com/svn
cd ~/.tmp-bare.git
git for-each-ref --format='%(refname)' refs/heads/tags | cut -d / -f 4 | while read ref
do
  git tag "$ref" "refs/heads/tags/$ref";
  git branch -D "tags/$ref";
done
