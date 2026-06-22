#!/bin/bash

APT_UPDATED=false
USE_APPTAINER=false

if command -v apptainer >/dev/null 2>&1 \
  && [[ -f "${BBTOOLS_SIF}" ]] \
  && [[ -f "${FASTP_SIF}" ]] \
  && [[ -f "${FASTQC_SIF}" ]]; then
  USE_APPTAINER=true
fi

apt_install_package() {
  local package="$1"

  if [[ "${APT_UPDATED}" == false ]]; then
    echo "Apptainer unavailable; updating apt package index"
    sudo apt-get update
    APT_UPDATED=true
  fi

  echo "Installing missing package: ${package}"
  sudo apt-get install -y "${package}"
}

ensure_command() {
  local command_name="$1"
  local package_name="$2"

  if ! command -v "${command_name}" >/dev/null 2>&1; then
    apt_install_package "${package_name}"
  fi

  command -v "${command_name}" >/dev/null 2>&1 \
    || { echo "Error: failed to install required command '${command_name}' via package '${package_name}'" >&2; exit 1; }
}

pipeline_runtime_banner() {
  if [[ "${USE_APPTAINER}" == true ]]; then
    echo "Runtime: Apptainer containers"
  else
    echo "Runtime: native tools via apt when missing"
  fi
}

run_fastqc() {
  if [[ "${USE_APPTAINER}" == true ]]; then
    apptainer exec --env "_JAVA_OPTIONS=-Xmx8g" "${FASTQC_SIF}" fastqc "$@"
  else
    ensure_command fastqc fastqc
    fastqc "$@"
  fi
}

run_fastp() {
  if [[ "${USE_APPTAINER}" == true ]]; then
    apptainer exec "${FASTP_SIF}" fastp "$@"
  else
    ensure_command fastp fastp
    fastp "$@"
  fi
}

run_reformat() {
  if [[ "${USE_APPTAINER}" == true ]]; then
    apptainer exec "${BBTOOLS_SIF}" reformat.sh "$@"
  else
    ensure_command reformat.sh bbmap
    reformat.sh "$@"
  fi
}
