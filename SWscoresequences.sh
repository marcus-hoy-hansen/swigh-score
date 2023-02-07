#!/bin/bash

while read p; do
  ./SWscore "$p" $2
done < $1
