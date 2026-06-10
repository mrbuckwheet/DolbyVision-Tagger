#!/bin/bash

CONFIG_DIR="/app/config"
CONFIG_FILE="$CONFIG_DIR/config.env"
LOG_DIR="$CONFIG_DIR/logs"
LOG_FILE="$LOG_DIR/dv_tagger.log"

COMPOSE_PUID=$PUID
COMPOSE_PGID=$PGID

mkdir -p "$CONFIG_DIR" "$LOG_DIR"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "⚙️ No config file discovered. Using defaults..."
    cat << EOF > "$CONFIG_FILE"
PUID="${COMPOSE_PUID:-1000}"
PGID="${COMPOSE_PGID:-1000}"
BINARIES_PATH="/usr/local/bin"
PLEX_TOKEN=""
PLEX_SERVER_URL="http://plex:32400"
PLEX_LIBRARIES="Movies"
GENERAL_LABEL="True"
PLEX_PATH_PREFIX="/Media/Movies"
LOCAL_PATH_PREFIX="/Movies"
CRON_SCHEDULE="50 6,18 * * *"
EOF
fi

source "$CONFIG_FILE"

USER_ID=${COMPOSE_PUID:-${PUID:-1000}}
GROUP_ID=${COMPOSE_PGID:-${PGID:-1000}}

echo "👤 Enforcing execution permissions for UID: $USER_ID, GID: $GROUP_ID"

if ! getent group abc >/dev/null; then
    groupadd -g "$GROUP_ID" abc
fi

if ! getent passwd abc >/dev/null; then
    useradd -u "$USER_ID" -g "$GROUP_ID" -m -s /bin/bash abc
fi

touch "$LOG_FILE"
chown -R abc:abc "$CONFIG_DIR"

if [ -n "$CRON_SCHEDULE" ]; then
    echo "$CRON_SCHEDULE root set -a && . $CONFIG_FILE && set +a && su -p abc -c '/usr/local/bin/python /app/mrbuckwheets_dv_tagger.py' >> $LOG_FILE 2>&1" > /etc/cron.d/dv-tagger
    chmod 0644 /etc/cron.d/dv-tagger
    echo "⏰ Background automation scheduled via cron expression: '$CRON_SCHEDULE'"
fi

cron

echo "🚀 Launching interactive WebUI on port 3636..."
exec python /app/app.py
