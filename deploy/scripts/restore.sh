#!/usr/bin/env bash
set -Eeuo pipefail
if [[ $# -ne 1 ]]; then echo "Usage: restore.sh /absolute/path/to/timestamped-backup" >&2; exit 64; fi
backup_dir="$(realpath "$1")"
backup_root="$(realpath "${NOREVIA_BACKUP_PATH:-/var/backups/norevia}")"
case "${backup_dir}" in "${backup_root}"/*) ;; *) echo "Backup must be beneath ${backup_root}" >&2; exit 65;; esac
[[ -f "${backup_dir}/database.dump" && -f "${backup_dir}/raw.tar.gz" && -f "${backup_dir}/SHA256SUMS" ]] || { echo "Incomplete backup" >&2; exit 66; }
(cd "${backup_dir}" && sha256sum --check SHA256SUMS)
echo "This replaces the target database. Type RESTORE to continue:"
read -r confirmation
[[ "${confirmation}" == "RESTORE" ]] || exit 1
pg_restore --clean --if-exists --no-owner --dbname="${NOREVIA_DATABASE_URL_SYNC:?Set a libpq-compatible restore URL}" "${backup_dir}/database.dump"
install -d -m 0750 "${NOREVIA_RAW_STORAGE_PATH:-/var/lib/norevia/raw}"
tar --extract --gzip --file="${backup_dir}/raw.tar.gz" --directory="${NOREVIA_RAW_STORAGE_PATH:-/var/lib/norevia/raw}"
