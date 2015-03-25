#!/bin/sh


# Manually patch and compile bash for systems like FC16 that don't have shellshock protection 
# availalbe through their package managers.

# sudo yum install patch byacc texinfo bison autoconf gettext ncurses-devel

VERSION1=4
VERSION2=2
VERSION_PATCH=52

if [ "$1" ]; then
    VERSION1="$1"
else
    echo "You probably want to rerun this script with your desired version and patch information like this:"
    echo "patch-bash.sh 4 2 52"
    echo "patch-bash.sh 4 1 16"
    echo "     OR"
    echo "patch-bash.sh 4 0 60"
fi

if [ "$2" ]; then
    VERSION2="$2"
fi

if [ "$3" ]; then
    VERSION_PATCH="$3"
fi

VERSION="$VERSION1.$VERSION2"

echo 'Downloading and compiling bash version '$VERSION' patch level '$VERSION_PATCH
echo 'If this is not what you want, you should cancel and rerun this script with your version and patch level digits as arguments...'  # 4.2


sudo cp /bin/bash /bin/bash.bak
mkdir -p ~/src/patch-bash
cd ~/src/patch-bash
wget https://ftp.gnu.org/pub/gnu/bash/bash-$VERSION.tar.gz
tar xvzf bash-$VERSION.tar.gz
cd bash-$VERSION
# git init .
# git add .
# git commit -am "download from https://ftp.gnu.org/pub/gnu/bash/bash-$VERSION.tar.gz"


for i in `seq 1 $VERSION_PATCH`;
do
    NUMBER=$(printf %03d $i)
    URI="https://ftp.gnu.org/pub/gnu/bash/bash-${VERSION}-patches/bash${VERSION1}${VERSION2}-$NUMBER"
    echo $URI
    curl $URI | patch -N -p0
done

echo "Make sure the PATCHLEVEL matches the LEVEL you requested in the 3rd command line argument to this script:" 
grep -E 'PATCHLEVEL\s+[0-9]+' patchlevel.h

./configure
make
make test

if [ -f "bash" ]; then
sudo mv /bin/bash /bin/bash.locked-by-running-processeses
sudo cp bash /bin/bash
fi
cd ..

echo 'Make sure this is the version you want!!!!!!!!!'
bash --version

echo 'If you find the word "vulnerable" anywhere below then something went wrong with your patch and you need to try again:'

env x='() { :;}; echo vulnerable to exploit 1' bash -c "echo this is a test"

# cd /tmp; env X='() { (a)=>\' bash -c "echo date"; cat echo

env -i X=' () { }; echo vulnerable to exploit 3' bash -c 'date'

bash -c 'true <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF' || echo "CVE-2014-7186 (exploit 4) vulnerable, redir_stack"

(for x in {1..200} ; do echo "for x$x in ; do :"; done; for x in {1..200} ; do echo done ; done) | bash || echo "CVE-2014-7187 (exploit 5) vulnerable, word_lineno"

