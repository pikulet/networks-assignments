#!/bin/bash

progName="IPAddress"
args="00010001001000100100010010001000"
ans="17.34.68.136"

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
