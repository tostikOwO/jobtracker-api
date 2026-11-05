#!/usr/bin/env bash
# Локальный PostgreSQL без root: бинарники лежат в ~/.local/share/pgrootless.
# Использование: scripts/pg.sh start|stop|status
set -euo pipefail

PGROOT="${JT_PGROOT:-$HOME/.local/share/pgrootless}"
PGHOME="$PGROOT/postgresql-18.6.1-x86_64-unknown-linux-gnu"
DATA="$PGROOT/data"
SOCK="$PGROOT/run"
PORT="${PGPORT:-55432}"

export PATH="$PGHOME/bin:$PATH"

case "${1:-status}" in
    start)
        mkdir -p "$SOCK"
        pg_ctl -D "$DATA" -l "$PGROOT/pg.log" \
            -o "-p $PORT -k $SOCK -c listen_addresses=127.0.0.1" start
        ;;
    stop)
        pg_ctl -D "$DATA" stop -m fast
        ;;
    status)
        pg_isready -h 127.0.0.1 -p "$PORT"
        ;;
    *)
        echo "usage: $0 {start|stop|status}" >&2
        exit 2
        ;;
esac
