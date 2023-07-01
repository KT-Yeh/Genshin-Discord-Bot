#!/bin/bash

if [ ! -d "data/bot" ]; then
  mkdir -p data/bot
fi
if [ ! -d "data/image" ]; then
  mkdir -p data/image
fi
if [ ! -d "data/font" ]; then
  mkdir -p data/font
fi
cp -rn assets/image/* data/image/
cp -rn assets/font/* data/font/
cp -rn configs/* data/

pid=0

term_handler() {
  if [ "$pid" -ne 0 ]; then
    kill -SIGTERM "$pid"
    wait "$pid"
  fi
  exit 143;
}

trap 'kill ${!}; term_handler' TERM

python main.py &
pid="$!"

while true
do
  tail -f /dev/null & wait ${!}
done