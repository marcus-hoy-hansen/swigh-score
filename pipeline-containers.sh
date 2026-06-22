#!/bin/bash

SWIGH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIF_DIR="$(cd "${SWIGH_DIR}/../singularities" && pwd)"

BBTOOLS_SIF="${SIF_DIR}/bbtools.sif"
FASTP_SIF="${SIF_DIR}/fastp.sif"
FASTQC_SIF="${SIF_DIR}/fastqc2.sif"
