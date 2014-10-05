#!/usr/bin/env bash
# Check for shell-shock vulnerabilities 1-5

cd ~/

echo 'If your bash version is 4.2.48 you are patched'
echo 'If your bash version is 4.1.16 you are patched'
echo 'Make sure the version below is the version you want!!!!!!!!!'
echo 'Your `bash --version` is:'
bash --version

echo 'If you find the word "VULNERABLE" anywhere below then something went wrong with your patch and you need to try again:'
echo

env x='() { :;}; echo VULNERABLE to exploit 1' bash -c "echo This is a test of exploit 1 and your shell seems to have passed"
echo

# echo "If you see the current date/time below then Exploit 3 may work on your shell. But this test still shows problems with my fully patched bash."
# cd /tmp; env X='() { (a)=>\' bash -c "echo date"; cat echo

env -i X=' () { }; echo VULNERABLE to exploit 3' bash -c 'date'
echo

bash -c 'true <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF' || echo "CVE-2014-7186 (Exploit 4) VULNERABLE, redir_stack"
echo

(for x in {1..200} ; do echo "for x$x in ; do :"; done; for x in {1..200} ; do echo done ; done) | bash || echo "CVE-2014-7187 (Exploit 5) VULNERABLE, word_lineno"
echo
