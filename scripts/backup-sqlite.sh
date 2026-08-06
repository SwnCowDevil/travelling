#!/bin/sh
set -eu

DATABASE_PATH=${TRAVEL_DATABASE_PATH:-/opt/travelling/backend/data/travel.db}
BACKUP_DIR=${TRAVEL_BACKUP_DIR:-/var/backups/travelling}
KEEP_DAYS=${TRAVEL_BACKUP_KEEP_DAYS:-14}

mkdir -p "$BACKUP_DIR"
STAMP=$(date +%Y%m%d-%H%M%S)
TARGET="$BACKUP_DIR/travel-$STAMP.db"
sqlite3 "$DATABASE_PATH" ".backup '$TARGET'"
sqlite3 "$TARGET" "PRAGMA integrity_check;" | grep -qx ok
find "$BACKUP_DIR" -type f -name 'travel-*.db' -mtime "+$KEEP_DAYS" -delete
echo "$TARGET"
