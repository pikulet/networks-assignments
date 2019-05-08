#!/bin/bash

port=${1:-8000}

echo "Server port: $port"

tmp="$(mktemp)"
cleanup() {
  yes | rm "$tmp*" 2> /dev/null
}
trap cleanup EXIT

sendReq() {
  echo "Requesting '$1'"
  ( printf "$1"; sleep 1 ) | netcat -c localhost "$port" > "$tmp" 
  local rtn="$?"
  if [[ "$rtn" != 0 ]]; then
    echo "Connection failed!"
  fi
  return "$rtn"
}

sendReq3() {
  echo "Requesting '$1' '$2' '$3'"
  ( printf "$1"; sleep 1; printf "$2"; sleep 1; printf "$3"; sleep 1 ) | netcat -c localhost "$port" > "$tmp" 
  local rtn="$?"
  if [[ "$rtn" != 0 ]]; then
    echo "Connection failed!"
  fi
  return "$rtn"
}

py3="/usr/local/Python-3.7/bin/python3"
splitRes() {
  local i="$1"
  local j="${2:-$i}"
  "$py3" -c "import sys;b=sys.stdin.buffer.read();a=b.split(b'  ',$i);sys.stdout.buffer.write(a[$j-1]+(b'  ' if $i>=$j else b''))" < "$tmp.o" > "$tmp"
  cat "$tmp"
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
testRawTail() {
  if ! cmp -s <(/usr/xpg4/bin/tail -c "$1" "$tmp") <(printf "$2"); then
    isPassed=0
    echo 'Binary content does not match.'
  fi
}
testIsPassed() {
  if [[ "$isPassed" == 1 ]]; then
    echo Test passed.
  else
    isBundlePassed=0
  fi
}

if grep -V 2> /dev/null | grep 'GNU grep' > /dev/null; then
  grep="grep"
else
  grep="ggrep"
fi

testBundle() {
  cp "$tmp" "$tmp.o"
  isBundlePassed=1
  echo '-- request 1 --'
  splitRes 1
  echo "Got response header:"
  $grep -o '.*  ' "$tmp"
  isPassed=1
  testStatus 404
  testEoh
  testIsPassed
  echo '-- request 2 --'
  splitRes 2
  echo "Got response header:"
  $grep -o '.*  ' "$tmp"
  isPassed=1
  testStatus 200
  testEoh
  testIsPassed
  echo '-- request 3 --'
  splitRes 2 3
  echo "Got response header:"
  $grep -o '.*  ' "$tmp"
  isPassed=1
  testStatus 200
  testCLen 6
  testEoh
  testContent "CS2105"
  testIsPassed
  if [[ "$isBundlePassed" == "1" ]]; then
    echo "-- Persistent connection testing passed --"
  else
    echo "-- Persistent connection testing failed --"
  fi
  echo
}

echo '-- Test 1: three requests sent in round trips --'
if sendReq3 "GET /file/cs2105.txt  " "POST /key/ModuleCode content-length 6  CS2105" "GET /key/ModuleCode  "; then
  testBundle
fi

echo '-- Test 2: three requests sent together --'
if sendReq "GET /file/cs2105.txt  POST /key/ModuleCode content-length 6  CS2105GET /key/ModuleCode  "; then
  testBundle
fi

echo '-- Test 3: requests splitted randomly and then sent --'
if sendReq3 "GET /file/cs210" "5.txt  POST /key/ModuleCode content-length 6  CS2105GE" "T /key/ModuleCode  "; then
  testBundle
fi

echo '-- Test 4: post raw bytes in content body --'
if sendReq $'POST /key/Raw content-length 5  \xff\x01\xfe\x02\xfd'; then
  echo "Got response header:"
  $grep -o '.*  ' "$tmp"
  isPassed=1
  testStatus 200
  testEoh
  testIsPassed
  echo
fi

echo '-- Test 5: get raw bytes in content body --'
if sendReq "GET /key/Raw  "; then
  echo "Got response header:"
  $grep -o '.*  ' "$tmp"
  isPassed=1
  testStatus 200
  testCLen 5
  testEoh
  testRawTail 5 $'\xff\x01\xfe\x02\xfd'
  testIsPassed
  echo
fi
