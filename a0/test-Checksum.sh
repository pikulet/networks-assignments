#!/bin/bash

progName="Checksum"
args="test.jpg"
ans='3237218320'

if python3 -c '' 2> /dev/null; then
  py3="python3"
else
  py3="/usr/local/Python-3.7/bin/python3"
fi

if diff <(eval "$py3" "$progName.py" $args) <(echo "$ans"); then
  echo '------'
  echo "$progName: test passed. The output is the same as the reference answer."
else
  echo '------'
  echo "$progName: test failed. The output is different from the reference answer."
fi
