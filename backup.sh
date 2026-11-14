#!/bin/sh
set -e
B=arox-backups-1997
D=/var/backups/arox
mkdir -p $D && chmod 700 $D
F=$D/arox-$(date -u +%Y%m%d-%H%M%S).sql.gz
T=$D/tmp.sql
docker exec aws_ai_postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner' > $T
[ -s $T ] || { echo "empty dump"; rm -f $T; exit 1; }
gzip -c $T > $F && rm -f $T
aws s3 cp $F s3://$B/db/ --region us-east-1 --only-show-errors
find $D -name 'arox-*.sql.gz' -mtime +7 -delete
echo "backup ok: $F"
