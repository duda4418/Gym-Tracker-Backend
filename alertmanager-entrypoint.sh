#!/bin/sh
set -eu

sed \
  -e "s|\${ALERTMANAGER_SMARTHOST}|${ALERTMANAGER_SMARTHOST}|g" \
  -e "s|\${ALERTMANAGER_EMAIL_FROM}|${ALERTMANAGER_EMAIL_FROM}|g" \
  -e "s|\${ALERTMANAGER_AUTH_USERNAME}|${ALERTMANAGER_AUTH_USERNAME}|g" \
  -e "s|\${ALERTMANAGER_AUTH_PASSWORD}|${ALERTMANAGER_AUTH_PASSWORD}|g" \
  -e "s|\${ALERTMANAGER_EMAIL_TO}|${ALERTMANAGER_EMAIL_TO}|g" \
  /etc/alertmanager/alertmanager.yml > /tmp/alertmanager.yml

exec /bin/alertmanager --config.file=/tmp/alertmanager.yml

