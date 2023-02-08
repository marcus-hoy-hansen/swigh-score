# swigh-score:
# Smith-Waterman immunoGlobulin heavy chain local alignment score tool

This tool performs a parallelized local alignment (Smith-Waterman) of a clonotype sequence from rearranged immunoglobulin heavy chain (IGH) loci to sequencing reads from IGH targeted sequencing. The output is the Smith-Waterman score normalized to the length of the shortest sequence for each comparison (clonotype versus each sequencing read length).

Please note that all reads below 200 bp are discarded. 


