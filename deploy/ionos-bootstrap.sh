#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

# One-time, root-only bootstrap for the standalone IONOS deployment.
# Existing application databases, Redis instances, units, and Nginx sites stay untouched.

readonly APP_ROOT="/home/mignon/apps/norevia"
readonly DOMAIN="norevia.amtklarpro.de"
readonly PG_VERSION="16"
readonly PG_CLUSTER="norevia"
readonly PG_PORT="5433"
readonly DB_NAME="norevia"
readonly DB_USER="norevia_app"
readonly REDIS_INSTANCE="norevia"
readonly REDIS_PORT="6380"
readonly API_PORT="8010"

if [[ ${EUID} -ne 0 ]]; then
  echo "Run this script with sudo." >&2
  exit 77
fi

for required in "${APP_ROOT}/.venv/bin/uvicorn" "${APP_ROOT}/.venv/bin/alembic" \
  "${APP_ROOT}/.venv/bin/norevia-pipeline" "${APP_ROOT}/apps/web/dist/index.html"; do
  [[ -e "${required}" ]] || { echo "Missing prepared artifact: ${required}" >&2; exit 66; }
done

cluster_exists() {
  pg_lsclusters --no-header 2>/dev/null | awk -v version="${PG_VERSION}" -v name="${PG_CLUSTER}" \
    '$1 == version && $2 == name { found = 1 } END { exit !found }'
}

port_is_listening() {
  ss -H -ltn "sport = :$1" | grep -q .
}

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  postgresql-${PG_VERSION}-postgis-3 certbot python3-certbot-nginx

if ! getent passwd norevia >/dev/null; then
  useradd --system --user-group --home-dir /var/lib/norevia --shell /usr/sbin/nologin norevia
fi

install -d -o norevia -g norevia -m 0750 \
  /var/lib/norevia /var/lib/norevia/raw /var/log/norevia /var/backups/norevia
install -d -o root -g norevia -m 0750 /etc/norevia

if ! cluster_exists; then
  if port_is_listening "${PG_PORT}"; then
    echo "Port ${PG_PORT} is already occupied; refusing to create the Norevia cluster." >&2
    exit 69
  fi
  pg_createcluster "${PG_VERSION}" "${PG_CLUSTER}" --port "${PG_PORT}" --start
fi

pg_conftool "${PG_VERSION}" "${PG_CLUSTER}" set port "${PG_PORT}"
pg_conftool "${PG_VERSION}" "${PG_CLUSTER}" set listen_addresses "localhost"
pg_conftool "${PG_VERSION}" "${PG_CLUSTER}" set max_connections "50"
pg_conftool "${PG_VERSION}" "${PG_CLUSTER}" set shared_buffers "256MB"
systemctl enable --now "postgresql@${PG_VERSION}-${PG_CLUSTER}.service"
systemctl restart "postgresql@${PG_VERSION}-${PG_CLUSTER}.service"

DB_PASSWORD="$(openssl rand -hex 32)"
if ! runuser -u postgres -- psql -p "${PG_PORT}" -d postgres -tAc \
  "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -qx 1; then
  runuser -u postgres -- createuser -p "${PG_PORT}" --login "${DB_USER}"
fi
runuser -u postgres -- psql -p "${PG_PORT}" -d postgres -v ON_ERROR_STOP=1 \
  -c "ALTER ROLE ${DB_USER} WITH LOGIN PASSWORD '${DB_PASSWORD}' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;"
if ! runuser -u postgres -- psql -p "${PG_PORT}" -d postgres -tAc \
  "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -qx 1; then
  runuser -u postgres -- createdb -p "${PG_PORT}" --owner "${DB_USER}" "${DB_NAME}"
fi
runuser -u postgres -- psql -p "${PG_PORT}" -d "${DB_NAME}" -v ON_ERROR_STOP=1 \
  -c "ALTER DATABASE ${DB_NAME} OWNER TO ${DB_USER};" \
  -c "CREATE EXTENSION IF NOT EXISTS postgis;"

if [[ ! -f "/etc/redis/redis-${REDIS_INSTANCE}.conf" ]] && port_is_listening "${REDIS_PORT}"; then
  echo "Port ${REDIS_PORT} is already occupied; refusing to configure Norevia Redis." >&2
  exit 69
fi
install -d -o redis -g redis -m 0750 "/var/lib/redis/${REDIS_INSTANCE}"
touch "/var/log/redis/redis-server-${REDIS_INSTANCE}.log"
chown redis:redis "/var/log/redis/redis-server-${REDIS_INSTANCE}.log"
chmod 0640 "/var/log/redis/redis-server-${REDIS_INSTANCE}.log"
cat > "/etc/redis/redis-${REDIS_INSTANCE}.conf" <<EOF
bind 127.0.0.1 ::1
protected-mode yes
port ${REDIS_PORT}
tcp-backlog 511
timeout 0
tcp-keepalive 300
supervised systemd
daemonize no
pidfile /run/redis-${REDIS_INSTANCE}/redis-server.pid
loglevel notice
logfile /var/log/redis/redis-server-${REDIS_INSTANCE}.log
databases 1
always-show-logo no
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis/${REDIS_INSTANCE}
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
appendfilename appendonly.aof
appenddirname appendonlydir
appendfsync everysec
EOF
chown root:redis "/etc/redis/redis-${REDIS_INSTANCE}.conf"
chmod 0640 "/etc/redis/redis-${REDIS_INSTANCE}.conf"
systemctl enable --now "redis-server@${REDIS_INSTANCE}.service"
systemctl restart "redis-server@${REDIS_INSTANCE}.service"
redis-cli -p "${REDIS_PORT}" ping | grep -qx PONG

cat > /etc/norevia/api.env <<EOF
NOREVIA_ENV=production
NOREVIA_DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@127.0.0.1:${PG_PORT}/${DB_NAME}
NOREVIA_DATABASE_URL_SYNC=postgresql://${DB_USER}:${DB_PASSWORD}@127.0.0.1:${PG_PORT}/${DB_NAME}
NOREVIA_REDIS_URL=redis://127.0.0.1:${REDIS_PORT}/0
NOREVIA_CORS_ORIGINS='["https://${DOMAIN}"]'
NOREVIA_OIDC_AUDIENCE=norevia-api
NOREVIA_ALLOW_DEVELOPMENT_IDENTITY=false
NOREVIA_RAW_STORAGE_PATH=/var/lib/norevia/raw
NOREVIA_BACKUP_PATH=/var/backups/norevia
NOREVIA_BACKUP_RETENTION_DAYS=30
NOREVIA_EUROSTAT_DATASETS=
NOREVIA_DESTATIS_DATASETS=
DESTATIS_USERNAME=
DESTATIS_PASSWORD=
EOF
chown root:norevia /etc/norevia/api.env
chmod 0640 /etc/norevia/api.env

cat > /etc/systemd/system/norevia-api.service <<EOF
[Unit]
Description=Norevia FastAPI service
Requires=postgresql@${PG_VERSION}-${PG_CLUSTER}.service redis-server@${REDIS_INSTANCE}.service
After=network-online.target postgresql@${PG_VERSION}-${PG_CLUSTER}.service redis-server@${REDIS_INSTANCE}.service
Wants=network-online.target

[Service]
Type=simple
User=norevia
Group=norevia
WorkingDirectory=${APP_ROOT}/apps/api
EnvironmentFile=/etc/norevia/api.env
Environment=HOME=/var/lib/norevia
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=${APP_ROOT}/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port ${API_PORT} --workers 2 --proxy-headers --forwarded-allow-ips=127.0.0.1
Restart=always
RestartSec=5
TimeoutStopSec=30
UMask=0027
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=read-only
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
ReadWritePaths=/var/lib/norevia /var/log/norevia
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/norevia-pipeline.service <<EOF
[Unit]
Description=Norevia official-data update pipeline
Requires=postgresql@${PG_VERSION}-${PG_CLUSTER}.service
After=network-online.target postgresql@${PG_VERSION}-${PG_CLUSTER}.service
Wants=network-online.target

[Service]
Type=oneshot
User=norevia
Group=norevia
WorkingDirectory=${APP_ROOT}
EnvironmentFile=/etc/norevia/api.env
Environment=HOME=/var/lib/norevia
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=${APP_ROOT}/deploy/scripts/update-data.sh
UMask=0027
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/var/lib/norevia/raw /var/log/norevia
EOF

cat > /etc/systemd/system/norevia-pipeline.timer <<'EOF'
[Unit]
Description=Run Norevia source checks every day

[Timer]
OnCalendar=*-*-* 03:15:00
RandomizedDelaySec=1800
Persistent=true

[Install]
WantedBy=timers.target
EOF

cat > /etc/systemd/system/norevia-backup.service <<EOF
[Unit]
Description=Back up the isolated Norevia database and raw archive
Requires=postgresql@${PG_VERSION}-${PG_CLUSTER}.service
After=postgresql@${PG_VERSION}-${PG_CLUSTER}.service

[Service]
Type=oneshot
User=norevia
Group=norevia
EnvironmentFile=/etc/norevia/api.env
Environment=HOME=/var/lib/norevia
ExecStart=${APP_ROOT}/deploy/scripts/backup.sh
UMask=0077
Nice=10
IOSchedulingClass=best-effort
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/var/backups/norevia
EOF

cat > /etc/systemd/system/norevia-backup.timer <<'EOF'
[Unit]
Description=Nightly Norevia backup

[Timer]
OnCalendar=*-*-* 02:10:00
RandomizedDelaySec=600
Persistent=true

[Install]
WantedBy=timers.target
EOF

chmod 0755 "${APP_ROOT}/deploy/scripts/backup.sh" "${APP_ROOT}/deploy/scripts/update-data.sh"
systemctl daemon-reload

set -a
# shellcheck disable=SC1091
source /etc/norevia/api.env
set +a
runuser -u norevia --preserve-environment -- /bin/bash -c \
  "cd '${APP_ROOT}/apps/api' && '${APP_ROOT}/.venv/bin/alembic' upgrade head && '${APP_ROOT}/.venv/bin/python' -m app.services.seed_catalog"

systemctl enable --now norevia-api.service norevia-pipeline.timer norevia-backup.timer

cat > /etc/nginx/sites-available/norevia <<EOF
limit_req_zone \$binary_remote_addr zone=norevia_api:10m rate=20r/s;

server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    root ${APP_ROOT}/apps/web/dist;
    index index.html;

    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=(self)" always;

    location /api/ {
        limit_req zone=norevia_api burst=40 nodelay;
        proxy_pass http://127.0.0.1:${API_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
    }

    location /health/ {
        proxy_pass http://127.0.0.1:${API_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location = /sw.js {
        expires -1;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        try_files \$uri =404;
    }

    location = /manifest.webmanifest {
        expires -1;
        add_header Cache-Control "no-cache";
        try_files \$uri =404;
    }

    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files \$uri =404;
    }

    location / {
        try_files \$uri \$uri/ /index.html;
        add_header Cache-Control "no-cache";
    }

    access_log /var/log/nginx/norevia.access.log;
    error_log /var/log/nginx/norevia.error.log warn;
}
EOF

ln -sfn /etc/nginx/sites-available/norevia /etc/nginx/sites-enabled/norevia
nginx -t
systemctl reload nginx

curl --fail --silent --show-error "http://127.0.0.1:${API_PORT}/health/ready" >/dev/null
certbot --nginx -d "${DOMAIN}" --redirect --non-interactive --agree-tos \
  --register-unsafely-without-email --keep-until-expiring
nginx -t
systemctl reload nginx

systemctl start norevia-backup.service

echo "Norevia bootstrap completed."
echo "Domain: https://${DOMAIN}"
echo "PostgreSQL cluster: ${PG_VERSION}/${PG_CLUSTER} on 127.0.0.1:${PG_PORT}"
echo "Redis instance: ${REDIS_INSTANCE} on 127.0.0.1:${REDIS_PORT}"
echo "API: 127.0.0.1:${API_PORT}"
