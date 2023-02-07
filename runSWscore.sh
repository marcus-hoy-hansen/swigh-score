#!/bin/bash


rm split.stack*

echo "Retrieving sequences of lengths above 200 bases for local Smith-Waterman alignment"
awk 'NR%4==2{b=$0} length(b)>200{print b;}' $1 > stack.fastq


echo "Splitting fastq file into chunks of $2 lines"
split -l $2 stack.fastq split.stack.

Files="split.stack.*"

for f in $Files
do
	echo "Performing local alignment of " $f 
	./SWscoresequences.sh $f $3 > $f.out.txt &
done

wait

echo "concatenating output..."
cat split.stack.*.out.txt | sort | uniq -c | tr -s " " "\t" | cut -f 2,3,4 | sort -n -s -k 1 | tac > $1".SWscore.out"

rm split.stack*
