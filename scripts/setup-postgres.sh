#!/usr/bin/env bash
# Установка и первичная настройка PostgreSQL для jobtracker-api.
# Запускать от root: sudo bash scripts/setup-postgres.sh
# Скрипт идемпотентен: повторный запуск ничего не ломает.
set -euo pipefail

PGDATA=/var/lib/postgres/data
DB_USER=jobtracker
DB_PASS=jobtracker
DB_NAME=jobtracker

echo "==> 1/5 установка пакета"
pacman -S --needed --noconfirm postgresql

echo "==> 2/5 инициализация кластера"
if [ ! -f "$PGDATA/PG_VERSION" ]; then
    install -d -o postgres -g postgres -m 700 "$PGDATA"
    sudo -iu postgres initdb -D "$PGDATA" --encoding=UTF8 --locale=C.UTF-8
else
    echo "    кластер уже инициализирован, пропускаю"
fi

echo "==> 3/5 запуск службы"
systemctl enable --now postgresql
# ждём, пока сервер начнёт принимать соединения
for _ in $(seq 1 15); do
    if sudo -iu postgres pg_isready -q; then break; fi
    sleep 1
done

echo "==> 4/5 роль $DB_USER"
if ! sudo -iu postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    sudo -iu postgres psql -c "CREATE ROLE $DB_USER LOGIN PASSWORD '$DB_PASS'"
else
    echo "    роль уже есть, пропускаю"
fi

echo "==> 5/5 база $DB_NAME"
if ! sudo -iu postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
    sudo -iu postgres createdb -O "$DB_USER" "$DB_NAME"
else
    echo "    база уже есть, пропускаю"
fi

echo
echo "READY: postgresql://$DB_USER@localhost:5432/$DB_NAME"
