#!/bin/bash

port=${1:-8000}

echo "Server port: $port"

tmp="$(mktemp)"
cleanup() {
  yes | rm "$tmp" 2> /dev/null
}
trap cleanup EXIT

sendReq() {
  echo ----------------
  echo "Requesting '$1'"
  ( printf "$1"; sleep 1 ) | netcat localhost "$port" > "$tmp" 
  local rtn="$?"
  if [[ "$rtn" != 0 ]]; then
    echo "Connection failed!"
  fi
  return "$rtn"
}

testStatus() {
  if ! $grep -q "^$1" "$tmp"; then
    isPassed=0
    echo "Wrong status code. Should be $1."
  fi
}
testCLen() {
  if ! $grep -q -i "^[0-9]*.* content-length $1 " "$tmp"; then
    isPassed=0
    echo "Wrong Content-Length. Should be $1"
  fi
}
testEoh() {
  if ! $grep -q '^[0-9]*.*  ' "$tmp"; then
    isPassed=0
    echo "Header is not ended properly."
  fi
}
testContent() {
  if ! $grep -q "  $1$" "$tmp"; then
    isPassed=0
    echo "File content is wrong."
  fi
}
testIsPassed() {
  if [[ "$isPassed" == 1 ]]; then
    echo Test passed.
  fi
}

if grep -V 2> /dev/null | grep 'GNU grep' > /dev/null; then
  grep="grep"
else
  grep="ggrep"
fi

# test 1: non-existent file
if sendReq "GET /file/cs2105.txt  "; then
  echo "Got response header:"
  $grep -o '.*  ' "$tmp"
  isPassed=1
  testStatus 404
  testEoh
  testIsPassed
fi
# test 2: existing file
if sendReq "GET /file/CS2105.txt  "; then
  echo "Got response header:"
  $grep -o '.*  ' "$tmp"
  isPassed=1
  testStatus 200
  testCLen 27
  testEoh
  testContent "Intro To Computer Networks!"
  testIsPassed
fi
# test 3: insert kv
if sendReq "POST /key/ModuleCode content-length 6  CS2105"; then
  echo "Got response header:"
  $grep -o '.*  ' "$tmp"
  isPassed=1
  testStatus 200
  testEoh
  testIsPassed
fi
# test 4: retrieve kv
if sendReq "GET /key/ModuleCode  "; then
  echo "Got response header:"
  $grep -o '.*  ' "$tmp"
  isPassed=1
  testStatus 200
  testCLen 6
  testEoh
  testContent "CS2105"
  testIsPassed
fi
# test 5: delete kv
if sendReq "DELETE /key/ModuleCode  "; then
  echo "Got response header:"
  $grep -o '.*  ' "$tmp"
  isPassed=1
  testStatus 200
  testCLen 6
  testEoh
  testContent "CS2105"
  testIsPassed
fi
# test 6: retrieve non-existent kv
if sendReq "GET /key/ModuleCode  "; then
  echo "Got response header:"
  $grep -o '.*  ' "$tmp"
  isPassed=1
  testStatus 404
  testEoh
  testIsPassed
fi

echo 
