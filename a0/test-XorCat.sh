#!/bin/bash

progName="XorCat"
args="test.jpg 210"

if python3 -c '' 2> /dev/null; then
  py3="python3"
else
  py3="/usr/local/Python-3.7/bin/python3"
fi

if cmp -s <(eval "$py3" "$progName.py" $args) ./test-jpg-xor210-ans; then
  echo '------'
  echo "$progName: test passed. The output is the same as the reference answer."
else
  echo '------'
  echo "$progName: test failed. The output is different from the reference answer."
fi
