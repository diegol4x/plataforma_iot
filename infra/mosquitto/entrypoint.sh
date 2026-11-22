#!/bin/sh
set -e

if [ -n "$MQTT_USERNAME" ] && [ -n "$MQTT_PASSWORD" ]; then
    touch /mosquitto/config/passwd
    chown mosquitto:mosquitto /mosquitto/config/passwd
    chmod 600 /mosquitto/config/passwd
    mosquitto_passwd -b /mosquitto/config/passwd "$MQTT_USERNAME" "$MQTT_PASSWORD"
fi

exec "$@"