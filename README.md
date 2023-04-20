# swigh-score:
# Smith-Waterman immunoGlobulin heavy chain local alignment score tool

This light-weight tool (swigh-score.sh) performs a parallelized local alignment (Smith-Waterman) of a clonotype sequence from rearranged immunoglobulin heavy chain (IGH) loci to sequencing reads from IGH targeted sequencing. The output of each alignment is the Smith-Waterman score normalized to the length of the shortest sequence for each comparison (clonotype versus sequencing read length). The Smith-Waterman alignment is written in C, whereas the wrapper is provided in bash/shell scripting. 

Parallization is achieved through a scatter gather approach, where the raw sequencing file is split into the number of requested threads (i.e. 31/63 threads used on 32/64 logical core CPU with PCI Express M.2 disks attached). Also, IGH sequencing contains duplicates that are counted and collapsed before analyses. In this way several million reads can brutely, but efficiently, be compared in few minutes following file split. 

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

Compare a clonotype sequence to control sequence spiked in known concentrations (e.g. 100 cells) to enable direct quantification of clonal B-cells (runs the analysis twice and reports the number of reads (>=98% match) for each compared to the total number of reads):

./swigh-compare [filename.fastq] [number of threads] [clonotype DNA string] [spike-in control DNA string]

To assign a Variable and Joining gene to the most frequent sequences (top 10) with a clonotype similarity threshold of 95%:

./swigh-clonotype [filename.fastq.out]

## Examples
./swigh-score test.fastq 31 CTTCTGGATACACCTTCACTAGTTATTCAATACATTGGGTGCGCCAGGCCCCCGGACAAGGGCTTGAGTGGATGGGATGGATCAACACTGGGAATGGTGACACAAGATATTCACAGAAATTCCAGGGCAGAGTCACCTTTACGAGGGACACATCCGCGACCACAGCCTACATGGAGCTGAGCAGCCTGACATCTGAAGACACGGCTGTATTTTATTGTGCGAGAGGGTTACGATTGCAAGAGGGATTATTATATGGGGATGACTTCTTTGACTACTGGGGCCAGGGATCCCG


./swigh-compare test.fastq 31  CTTCTGGATACACCTTCACTAGTTATTCAATACATTGGGTGCGCCAGGCCCCCGGACAAGGGCTTGAGTGGATGGGATGGATCAACACTGGGAATGGTGACACAAGATATTCACAGAAATTCCAGGGCAGAGTCACCTTTACGAGGGACACATCCGCGACCACAGCCTACATGGAGCTGAGCAGCCTGACATCTGAAGACACGGCTGTATTTTATTGTGCGAGAGGGTTACGATTGCAAGAGGGATTATTATATGGGGATGACTTCTTTGACTACTGGGGCCAGGGATCCCG  CTTCTGGAGGCACCTTCAGCAGCTATGCTATCAGCTGGGTGCGACAGGCCCCTGGACAAGGGCTTGAGTGGATGGGAGGGATCATCCCTATCTTTGGTACAGCAAACTACGCACAGAAGTTCCAGGGCAGAGTCACGATTACCGCGGACGAATCCACGAGCACAGCCTACATGGAGCTGAGCAGCCTGAGATCTGAGGACACGGCCGTGTATTACTGTGCGAGAGATAGGCGCGGGGAATGGCCTCCCTCGGATTACTACTACTACTACTACATGGACGTCTGGGGCAAAGGGACCAC


./swigh-clonotype test.fastq.out

## Updating local version
You may wish to update your local version, e.g., using the following command (warning, overwrites any changes):


cd swigh-score

git stash

git pull origin main




