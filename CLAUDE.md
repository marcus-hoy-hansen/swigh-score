# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

After cloning, compile the C binaries and set permissions:

```bash
chmod u+x config && ./config
```

This compiles `bin/SWscore.c` → `bin/SWscore` and `bin/q-filter.c` → `quality-filter`, and sets executable bits on all scripts.
It also writes `pipeline-containers.sh`, which hardcodes the shared SIF directory used by the pipeline wrappers.

To rebuild only the hyperthreaded scorer:
```bash
gcc -O2 -pthread -o bin/SWscore_hyperthreaded bin/SWscore_hyperthreaded.c
```

## Tool Overview

All scripts must be run from the repo root — they reference `bin/` via relative paths.

| Script | Purpose |
|--------|---------|
| `swigh-score` | SW-align one clonotype against all reads in a FASTQ |
| `swigh-report` | Summarise a `.out` file: similarity histogram + top V/J |
| `swigh-clonotype-sequence` | Best V/J gene match for a given DNA sequence |
| `swigh-clonotype-random` | V or J gene usage from a random sample of reads |
| `swigh-clonotype-amplicon` | V/J of the most recurrent read (amplicon mode) |
| `swigh-clonotype-exhaustive` | Best V or J per unique read across the whole file |
| `swigh-igl-pipeline` | End-to-end pipeline: QC → trim → merge → exhaustive IGL |
| `bin/lookup-ig-gene` | Look up IMGT V/J gene sequences by name |

## Key Data Flow

```
FASTQ
  └─ swigh-score          → <file>.out   (SW score per unique read + count)
       └─ swigh-report    → similarity table + swigh-clonotype-sequence call
  └─ swigh-clonotype-*    → gene assignment tables (.txt / .tsv)
```

`swigh-score` deduplicates reads before alignment (by default), joins scores back to counts, and outputs one line per unique sequence sorted by swigh-score descending.

`swigh-clonotype-exhaustive` calls `bin/swigh-clonotype2flatfiles` per unique sequence via `xargs -P` (workers) with `-t` SW threads each, then aggregates best-hit gene assignments.

## IMGT Gene Resources

Flat-text reference tables live in `bin/`:
- `igmt-{igh,igk,igl}-{vgene,jgene}-{name,sequence}.txt` — parallel line-indexed files (name[n] ↔ sequence[n])
- IGH also has `dgene` files
- `bin/igmt_format.py` regenerates these from the IMGT FASTA

All clonotype tools default to `--locus igh`; pass `--locus igk` or `--locus igl` to switch.

## Pipeline Runtime

The pipeline wrappers source `pipeline-containers.sh`, which points at `../singularities/` for:

| Tool | SIF |
|------|-----|
| FastQC | `fastqc2.sif` (v0.11.9 — `fastqc.sif` is broken, do not use) |
| fastp | `fastp.sif` (v1.3.3) |
| BBtools | `bbtools.sif` (bbmerge, reformat) |

If `apptainer` is available and those SIF files exist, the pipeline uses the containers.
If not, it falls back to native commands and attempts to install missing tools with:

```bash
sudo apt-get update
sudo apt-get install -y fastqc fastp bbmap
```

This fallback assumes a Debian/Ubuntu-style system with `sudo`.

Run the IGL pipeline with:
```bash
cd <dir-containing-fastqs>
/path/to/swigh-igl-pipeline <base>
# e.g. ../swigh-igl-pipeline 22-0453-00_S4
```

Run the general pipeline with either a sample base or a forward read:

```bash
cd <dir-containing-fastqs>
/path/to/swigh-pipeline --sample 22-0453-00_S4
/path/to/swigh-pipeline --input 23-0492-s1_S2_L001_R1_001.fastq
/path/to/swigh-pipeline --input test10k.fastq --paired-end false
```

Paired-end `--sample` accepts either `.fastq.gz` or `.fastq` files named `<base>_L001_R1_001...` and `<base>_L001_R2_001...`.
Paired-end `--input` expects the R1 filename to contain `_R1_`; R2 is inferred by replacing that token with `_R2_`. Output goes to `$PWD/<base>/`.

**BBmerge must run with `threads=1`** — its multithreaded FASTQ reader has a race condition that drops read pairs silently. fastp intermediates are written uncompressed (`.fastq`) for the same reason.

## Swigh-score Output Format

Columns: `sequence  similarity  SW_score  aligned_bases  swigh_score  count`

`swigh_score` = SW score normalised to the shorter of the two sequences. Sorted descending by swigh_score then count.
