#!/bin/bash

export PROXY_URL="${PROXY_URL}"

exec /app/duck2api "$@"
