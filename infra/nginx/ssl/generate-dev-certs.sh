#!/bin/bash
# Generate self-signed TLS certificates for development.
# In production, use Let's Encrypt via cert-manager.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout "${SCRIPT_DIR}/key.pem" \
    -out "${SCRIPT_DIR}/cert.pem" \
    -subj "/C=ES/ST=Madrid/L=Madrid/O=VerifID/OU=Dev/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1"

echo "Dev TLS certificates generated in ${SCRIPT_DIR}/"
