# swigh-score:
# Smith-Waterman immunoGlobulin heavy chain local alignment score tool

This light-weight tool (swigh-score.sh) performs a parallelized local alignment (Smith-Waterman) of a clonotype sequence from rearranged immunoglobulin heavy chain (IGH) loci to sequencing reads from IGH targeted sequencing. The output of each alignment is the Smith-Waterman score normalized to the length of the shortest sequence for each comparison (clonotype versus sequencing read length). The Smith-Waterman alignment is written in C, whereas the wrapper is provided in bash/shell scripting. 

Parallization is achieved through a scatter gather approach, where the raw sequencing file is split into the number of requested processes (i.e. 31/63 processes used on 32/64 logical core CPU with PCI Express M.2 disks attached or HPC vCPU). Also, IGH sequencing contains duplicates that are counted and collapsed before analyses. In this way several million reads can brutely, but efficiently, be compared in few minutes following file split. 

Please note that all sequencing reads below 200 bp are filtered out as IGH VDJ rearranged sequences below this threshold are generally truncated or non-informative. Currently, output summary uses a similarity threshold of 98%, but can be adjusted. Work in progress to include tabulated 90–100% sequencing similarity. 

## Get started
Download the script folder from github:

git clone https://github.com/marcus-hoy-hansen/swigh-score

Go the folder and configure the scripts (compiling the C code on linux platforms and changing permissions of executables):

cd swigh-score

chmod u+x config

./config


## Important commands
To Compare a clonotype sequence to reads in fastq file format: 

./swigh-score [filename.fastq] [number of threads] [clonotype DNA string]

To report the distribution of sequencing matches accoring to similarity-level as well as the most likely IGHV and IGHJ gene usage. Note that this tool uses the fastq.out-file, which is generated by the swigh-score command:

./Swigh-report [file.fastq.out]

To assertain the population of Variable (IGHV) and/or Joining (IGHJ) genes in a fastq file based on a random subset of 1000 sequences from a fastq-file:

./swigh-clonotype-random [file.fastq] [threads] [vgene/jgene]

To instead assign the likely IGHV and IGHJ usage of the most frequently occurring sequence/amplicon based on all reads, use the following command:

./swigh-clonotype-amplicon [file.fastq] [optional: number of reads to include]

To assertain the highest matching Variable (IGHV) and Joining (IGHJ) genes to any given clonotype DNA sequence:

./swigh-clonotype-sequence [DNA sequence]

Note that this tool is at the experimental prototype stage and may in some cases misclassify the polymorphism, while assigning the correct V and J. The tool is also suitable for the more error-prone Oxford Nanopore long-read sequencing.

## Examples
./swigh-score test.fastq 31 GCGTCTGGATTCACCTTCAGTGACTACTACATGGGCTGGATCCGCCTGGCTCCAGGGAGGGGGCTGGAGTGGATCTCATTCATTAGCCGAACGGGTAGTCACACAAACACCGCGGACTCTGTGAAGGGCCGATTCAGCATCTCCAGAGACAACGCCAACAATTTACTGTATCTACAAATGAACGGCCTGAGAGTCGAGGACACGGCTTTATATTACTGTGCGAGAGGGGGCCAGGTCAACTGGGAATTACCTGACTTCTGGGGCCAGGGAACCCT

./swigh-report test.fastq.out

./swigh-clonotype-random test.fastq 31 vgene

./swigh-clonotype-amplicon test.fastq

./swigh-clonotype-sequence GCGTCTGGATTCACCTTCAGTGACTACTACATGGGCTGGATCCGCCTGGCTCCAGGGAGGGGGCTGGAGTGGATCTCATTCATTAGCCGAACGGGTAGTCACACAAACACCGCGGACTCTGTGAAGGGCCGATTCAGCATCTCCAGAGACAACGCCAACAATTTACTGTATCTACAAATGAACGGCCTGAGAGTCGAGGACACGGCTTTATATTACTGTGCGAGAGGGGGCCAGGTCAACTGGGAATTACCTGACTTCTGGGGCCAGGGAACCCT

## Updating local version
You may wish to update your local version, e.g., using the following command (warning, overwrites any changes):


cd swigh-score

git stash

git pull origin main




