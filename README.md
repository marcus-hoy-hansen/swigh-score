# swigh-score:
# Smith-Waterman immunoGlobulin heavy chain local alignment score tool

This light-weight tool (swigh-score.sh) performs a parallelized local alignment (Smith-Waterman) of a clonotype sequence from rearranged immunoglobulin heavy chain (IGH) loci to sequencing reads from IGH targeted sequencing. The output of each alignment is the Smith-Waterman score normalized to the length of the shortest sequence for each comparison (clonotype versus sequencing read length). The Smith-Waterman alignment is written in C, whereas the wrapper is provided in bash/shell scripting. 

Parallization is achieved through a scatter gather approach, where the raw sequencing file is split into the number of requested threads (i.e. 31/63 threads used on 32/64 logical core CPU and PCI Express M.2 disks). Also, IGH sequencing contains duplicates that are counted and collapsed before analyses. In this way several million reads can brutely be compared in few minutes following file split. 

Please note that all sequencing reads below 200 bp are filtered out as IGH VDJ rearranged sequences below this threshold are generally truncated or non-informative.  


