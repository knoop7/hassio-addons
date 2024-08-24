#!/bin/bash

export PROXY_URL="${proxy_url}"

exec /app/duck2api "$@"
