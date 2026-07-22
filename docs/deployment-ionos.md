# IONOS Ubuntu production deployment (without Docker)

This deployment follows the repository's explicit no-Docker exception. Nginx serves the built PWA and terminates TLS; systemd isolates FastAPI, scheduled source checks, and backups. PostgreSQL/PostGIS and Redis use the Ubuntu packages and listen only on localhost.

## 1. Provision and secure the VPS

Use a supported Ubuntu LTS release, create an SSH-key-only administrator, disable root/password SSH login, and point the production DNS A/AAAA records at the VPS.

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y nginx postgresql postgresql-contrib postgis redis-server python3.12-venv python3-pip nodejs npm certbot python3-certbot-nginx ufw unattended-upgrades git curl
sudo adduser --system --group --home /var/lib/norevia norevia
sudo install -d -o norevia -g norevia -m 0750 /opt/norevia /var/lib/norevia/raw /var/log/norevia /var/backups/norevia
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo dpkg-reconfigure -plow unattended-upgrades
```

Do not open ports 5432, 6379, 8000, or 5173. Confirm with `sudo ss -lntup` and `sudo ufw status verbose`.

## 2. Database and Redis

```bash
sudo -u postgres createuser --pwprompt norevia
sudo -u postgres createdb --owner=norevia norevia
sudo -u postgres psql -d norevia -c 'CREATE EXTENSION IF NOT EXISTS postgis;'
sudo systemctl enable --now postgresql redis-server
```

Set `bind 127.0.0.1 ::1`, `protected-mode yes`, `supervised systemd`, and an appropriate `maxmemory-policy allkeys-lru` in `/etc/redis/redis.conf`, then restart Redis. Keep PostgreSQL `listen_addresses = 'localhost'`. Tune connections and memory for the VPS size; do not use development credentials.

## 3. Application release

```bash
sudo -u norevia git clone https://github.com/mignoncharly/norevia.git /opt/norevia/releases/initial
sudo -u norevia ln -s /opt/norevia/releases/initial /opt/norevia/current
sudo -u norevia python3.12 -m venv /opt/norevia/venv
sudo -u norevia /opt/norevia/venv/bin/pip install -e '/opt/norevia/current/apps/api' -e '/opt/norevia/current/pipelines'
cd /opt/norevia/current
sudo -u norevia npm ci
sudo -u norevia npm run build
cd /opt/norevia/current/apps/api
sudo -u norevia /opt/norevia/venv/bin/alembic upgrade head
sudo -u norevia /opt/norevia/venv/bin/python -m app.services.seed_catalog
```

Create `/etc/norevia/api.env` owned by root:norevia with mode `0640`:

```dotenv
NOREVIA_ENV=production
NOREVIA_DATABASE_URL=postgresql+asyncpg://norevia:REPLACE_WITH_ENCODED_PASSWORD@127.0.0.1:5432/norevia
NOREVIA_DATABASE_URL_SYNC=postgresql://norevia:REPLACE_WITH_ENCODED_PASSWORD@127.0.0.1:5432/norevia
NOREVIA_REDIS_URL=redis://127.0.0.1:6379/0
NOREVIA_CORS_ORIGINS=["https://norevia.example.com"]
NOREVIA_OIDC_ISSUER=https://identity.example.com/
NOREVIA_OIDC_AUDIENCE=norevia-api
NOREVIA_ALLOW_DEVELOPMENT_IDENTITY=false
NOREVIA_RAW_STORAGE_PATH=/var/lib/norevia/raw
NOREVIA_BACKUP_PATH=/var/backups/norevia
NOREVIA_BACKUP_RETENTION_DAYS=30
NOREVIA_EUROSTAT_DATASETS=
NOREVIA_DESTATIS_DATASETS=
DESTATIS_USERNAME=
DESTATIS_PASSWORD=
```

Never commit this file. Percent-encode reserved password characters in URLs. Enable source datasets only after reviewed mappings exist.

## 4. Services, reverse proxy, and TLS

Replace `norevia.example.com` in the Nginx file first.

```bash
sudo chmod 0750 /opt/norevia/current/deploy/scripts/*.sh
sudo cp /opt/norevia/current/deploy/systemd/* /etc/systemd/system/
sudo cp /opt/norevia/current/deploy/nginx/norevia.conf /etc/nginx/sites-available/norevia
sudo ln -s /etc/nginx/sites-available/norevia /etc/nginx/sites-enabled/norevia
sudo rm /etc/nginx/sites-enabled/default
sudo cp /opt/norevia/current/deploy/logrotate-norevia /etc/logrotate.d/norevia
sudo nginx -t
sudo certbot --nginx -d norevia.example.com --redirect --agree-tos -m operations@example.com
sudo systemctl daemon-reload
sudo systemctl enable --now norevia-api.service norevia-pipeline.timer norevia-backup.timer nginx
```

Certbot installs automatic renewal. Verify it with `sudo certbot renew --dry-run`.

## 5. Health, logs, and monitoring

```bash
curl --fail https://norevia.example.com/health/live
curl --fail https://norevia.example.com/health/ready
systemctl status norevia-api norevia-pipeline.timer norevia-backup.timer
journalctl -u norevia-api --since today
sudo nginx -t
sudo logrotate --debug /etc/logrotate.d/norevia
```

Configure the IONOS monitoring/alerting service or another external uptime checker against both health URLs. Alert on HTTP failure, disk usage above 80%, backup age above 26 hours, PostgreSQL availability, certificate expiry below 21 days, memory pressure, and repeated systemd restarts. Journal retention is configured in `/etc/systemd/journald.conf`; use `SystemMaxUse=1G` or a capacity-appropriate limit.

## 6. Backups and restore drill

The timer creates a custom-format PostgreSQL dump, compressed immutable raw archive, and SHA-256 manifest nightly. Copy `/var/backups/norevia` to a different failure domain (IONOS Object Storage or another encrypted remote) after each successful backup. A backup remaining on the VPS is not disaster recovery.

Test quarterly on a separate database:

```bash
sudo systemctl start norevia-backup.service
sudo systemctl status norevia-backup.service
sudo -u postgres createdb --owner=norevia norevia_restore_test
sudo -u norevia env NOREVIA_DATABASE_URL_SYNC='postgresql://norevia:PASSWORD@127.0.0.1/norevia_restore_test' /opt/norevia/current/deploy/scripts/restore.sh /var/backups/norevia/YYYYMMDDTHHMMSSZ
sudo -u postgres psql -d norevia_restore_test -c 'SELECT count(*) FROM observations;'
sudo -u postgres dropdb norevia_restore_test
```

The restore script verifies checksums and requires typing `RESTORE` because it uses `pg_restore --clean` against the selected target.

## 7. Zero/low-downtime releases and rollback

Build each commit in `/opt/norevia/releases/<git-sha>`, install dependencies, run tests, build the PWA, and run `alembic upgrade head`. Switch `/opt/norevia/current` atomically to the new release and restart `norevia-api`. Retain at least the previous two releases. Database downgrades are not automatic: prefer forward fixes; test any downgrade on a restored backup before production.

```bash
sudo systemctl restart norevia-api
sudo systemctl reload nginx
curl --fail https://norevia.example.com/health/ready
```

If health fails, repoint `current` to the last known-good application release and restart the API. Do not roll back the database unless the migration's documented downgrade has been tested and is compatible.
