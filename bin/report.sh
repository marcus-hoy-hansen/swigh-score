#!/bin/bash

f=$1.report.txt
if test -f $f; then 
	rm $f
fi

touch $f

echo $'Clonal reads\tSpike-in reads\tTotal reads' >> $f
clone=$(cat clone$1 | awk '$2>=0.98 {print $3}' | paste -s -d+ - | bc)
spike=$(cat spikein$1 | awk '$2>=0.98 {print $3}' | paste -s -d+ - | bc)
total=$(cat clone$1 | awk '$2>=0 {print $3}' | paste -s -d+ - | bc)
echo -n $clone$'\t'$spike$'\t'$total$'\n' >> $f

