#!/bin/bash


./swigh-score.sh $1 8 $2 clone
./swigh-score.sh $1 8 $3 spikein
bin/report.sh $1'.out'

