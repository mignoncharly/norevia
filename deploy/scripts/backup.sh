#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
backup_root="${NOREVIA_BACKUP_PATH:-/var/backups/norevia}"
raw_root="${NOREVIA_RAW_STORAGE_PATH:-/var/lib/norevia/raw}"
backup_root="$(realpath -m "${backup_root}")"
raw_root="$(realpath -m "${raw_root}")"
case "${backup_root}" in /var/backups/norevia|/var/backups/norevia/*) ;; *) echo "Unsafe backup root: ${backup_root}" >&2; exit 65;; esac
case "${raw_root}" in /var/lib/norevia/raw|/var/lib/norevia/raw/*) ;; *) echo "Unsafe raw root: ${raw_root}" >&2; exit 65;; esac
retention_days="${NOREVIA_BACKUP_RETENTION_DAYS:-30}"
[[ "${retention_days}" =~ ^[0-9]{1,4}$ ]] || { echo "Invalid retention period" >&2; exit 65; }
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
destination="${backup_root}/${stamp}"
install -d -m 0700 "${destination}"
pg_dump --dbname="${NOREVIA_DATABASE_URL_SYNC:?Set a libpq-compatible backup URL}" --format=custom --compress=9 --file="${destination}/database.dump"
tar --create --gzip --file="${destination}/raw.tar.gz" --directory="${raw_root}" .
sha256sum "${destination}/database.dump" "${destination}/raw.tar.gz" > "${destination}/SHA256SUMS"
find "${backup_root}" -mindepth 1 -maxdepth 1 -type d -mtime +"${retention_days}" -print -exec rm -rf -- {} +
