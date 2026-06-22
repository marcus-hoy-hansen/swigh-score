#!/bin/bash

REF=$2
READS=$1
THREADS=${3:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)}

bin/SWscore_hyperthreaded "$REF" "$READS" "$THREADS"
