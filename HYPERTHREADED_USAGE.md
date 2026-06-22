swigh-score (hyperthreaded) quickstart
======================================

Setup
-----
- Ensure `bin/SWscore_hyperthreaded` is built (`gcc -O2 -pthread -o bin/SWscore_hyperthreaded bin/SWscore_hyperthreaded.c`).
- FASTQ test file is available (e.g., `gzip -dc test.fastq.gz > test.fastq`).

Core commands
-------------
- Align clonotype to reads:
  - `./swigh-score -i <file.fastq> -r <CLONOTYPE> -t <threads> [-o prefix] [-B batch] [-b band] [--no-dedup]`
  - Positional legacy still works: `./swigh-score <file.fastq> <threads> <CLONOTYPE> [prefix]`
  - Outputs: `tmp/<file>.SWscore.out` (raw scores), `<prefix><file>.out` (joined with counts).
  - Example:  
    `./swigh-score -i test.fastq -t 24 -r GACTACTACATGGGCTGGATCCGCCTGGCTCCAGGGAGGGGGCTGGAGTGGATCTCATTCATTAGCCGAACGGGTAGTCACACAAACACCGCGGACTCTGTGAAGGGCCGATTCAGCATCTCCAGAGACAACGCCAACAATTTACTGTATCTACAAATGAACGGCCTGAGAGTCGAGGACACGGCTTTATATTACTGTGCGAGAGGGGGCCAGGTCAACTGGGAATTACCTGACTTCTGG`
- Report similarity distribution and top V/J from the `.out` file:
  - `./swigh-report <file.fastq.out>`
- Random clonotyping (default 1000 reads, V-gene):
  - `./swigh-clonotype-random -i <file.fastq> -t <threads> [-g vgene|jgene] [-n sample_size]`
  - Outputs `<file>.<gene>.txt` with counts.
- Amplicon clonotyping (most recurrent sequence):
  - `./swigh-clonotype-amplicon -i <file.fastq> [-t threads] [-b band] [optional_read_count]`
- Gene matches for a clonotype sequence:
  - `./swigh-clonotype-sequence -r <CLONOTYPE> [-t threads] [-n top_n] [-b band]`
- Lookup IMGT V/J gene sequences (Homo sapiens tables in `bin/`):
  - `bin/lookup-ig-gene -l IGH|IGK|IGL [-v VGENE] [-j JGENE] [--output-name]`

Notes
-----
- Thread count defaults to detected cores if `-t` is omitted.
- `-b/--band` sets banded Smith–Waterman half-width; `0` = full SW.
- Output columns from the scorer match legacy format: `<read>  <similarity>  <SW score>  <aligned bases>  <swigh-score>`.
- Pandoc helper: if you want a PDF/HTML version, activate the bundled env and run, e.g., `source pandoc_env/bin/activate && pandoc -s HYPERTHREADED_USAGE.md -o HYPERTHREADED_USAGE.pdf`.
- `--no-dedup` skips collapsing duplicate reads (useful on very diverse datasets); default is to deduplicate for speed on clonal data.
