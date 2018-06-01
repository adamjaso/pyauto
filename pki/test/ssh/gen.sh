#!/bin/bash
dirname=$(dirname $0)
for bit in 1024 2048 4096 ; do
ssh-keygen -P '' -b $bit -t rsa -f $dirname/$typ-$bit
done
