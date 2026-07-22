#!/usr/bin/env bash
set -Eeuo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/../.." && pwd)"
pipeline_bin="${NOREVIA_PIPELINE_BIN:-${repo_root}/.venv/bin/norevia-pipeline}"
raw_root="${NOREVIA_RAW_STORAGE_PATH:-/var/lib/norevia/raw}"
IFS=',' read -ra eurostat_datasets <<< "${NOREVIA_EUROSTAT_DATASETS:-}"
for dataset in "${eurostat_datasets[@]}"; do [[ -n "${dataset}" ]] && "${pipeline_bin}" eurostat "${dataset}" --raw-root "${raw_root}"; done
IFS=',' read -ra destatis_datasets <<< "${NOREVIA_DESTATIS_DATASETS:-}"
for dataset in "${destatis_datasets[@]}"; do [[ -n "${dataset}" ]] && "${pipeline_bin}" destatis "${dataset}" --raw-root "${raw_root}"; done
