#!/usr/bin/env bash
ifconfig eth0 | grep 'inet addr:' | cut -d \: -f 2 | cut -d ' ' -f 1