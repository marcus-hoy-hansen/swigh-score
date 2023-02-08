#!/bin/bash

# USAGE: ./swigh-score.sh filename threads DNAstring 
# STOPPING PROCESS: killall -9 swigh-score

mkdir tmp

echo "Retrieving sequences of lengths above 200 bases for local Smith-Waterman alignment"
awk 'NR%4==2 {a=$2; if(length($a)>200) print $a}' $1 | sort | uniq -c | tr -s " " "\t" | awk '{ print $2"\t"$1}' | sort > tmp/counts.txt
cut -f1 tmp/counts.txt > tmp/stack.fastq

n=$(< tmp/counts.txt wc -l)
lines=$(awk -v num=$n -v threads=$2 'BEGIN {print int(num/threads)}')

echo $lines
echo "Splitting fastq file into chunks of $lines lines"
split -l $lines tmp/stack.fastq tmp/split.stack.

Files="split.stack.*"

for f in 'tmp/'$Files
do
	echo "Performing local alignment of " $f 
	bin/SWscoresequences.sh $f $3 > $f.out.txt &
done

wait

echo "concatenating output..."
cat tmp/split.stack.*.out.txt | sort > tmp/$1".SWscore.out" 
join tmp/$1".SWscore.out" tmp/counts.txt | sort -k2nr > $4$1".out"

rm -r tmp


