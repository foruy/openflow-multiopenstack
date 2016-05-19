#!/bin/bash
set -e

DATADIR=/var/lib/mysql
exist=0

if [ -z "$(ls -A $DATADIR)" ]; then
    mysql_install_db --user=mysql --datadir="$DATADIR"
    exist=1
fi

chown -R mysql:mysql "$DATADIR"

/etc/init.d/mysql start

if [ "$exist" -eq 1 ]; then
    mysql < /tmp/scripts/db.sql
fi
