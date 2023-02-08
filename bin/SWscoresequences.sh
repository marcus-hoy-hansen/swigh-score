#!/bin/bash

while read p; do
  bin/SWscore "$p" $2
done < $1





