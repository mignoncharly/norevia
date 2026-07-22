#!/usr/bin/env bash
set -Eeuo pipefail
raw_root="${NOREVIA_RAW_STORAGE_PATH:-/var/lib/norevia/raw}"
IFS=',' read -ra eurostat_datasets <<< "${NOREVIA_EUROSTAT_DATASETS:-}"
for dataset in "${eurostat_datasets[@]}"; do [[ -n "${dataset}" ]] && /opt/norevia/venv/bin/norevia-pipeline eurostat "${dataset}" --raw-root "${raw_root}"; done
IFS=',' read -ra destatis_datasets <<< "${NOREVIA_DESTATIS_DATASETS:-}"
for dataset in "${destatis_datasets[@]}"; do [[ -n "${dataset}" ]] && /opt/norevia/venv/bin/norevia-pipeline destatis "${dataset}" --raw-root "${raw_root}"; done
