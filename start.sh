#!/bin/bash
set -e
cd /opt/arox
aws ssm get-parameters-by-path --path /arox/ --with-decryption --region us-east-1 \
  --query "Parameters[].[Name,Value]" --output text \
| awk '{n=toupper($1); sub("/AROX/","",n); gsub("-","_",n); print n"="$2}' > /run/arox.env
chmod 600 /run/arox.env
docker compose --env-file /run/arox.env up -d --build
rm -f /run/arox.env
