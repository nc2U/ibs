#!/bin/bash
DATE=$(date +"%Y-%m-%d")
SQL_FILE=/var/backups/backup-${DATE}.sql

# (2) in case you run this more than once a day,
# remove the previous version of the file
# shellcheck disable=SC2046
find /var/backups -name "*.sql" -mtime +2 -type f -delete

# (3) do the mysql database backup (dump)
mariadb-dump -u"${USER}" -p"${PASSWORD}" "${DATABASE}" --ignore-table="${DATABASE}".django_migrations > "${SQL_FILE}"

# 백업이 성공했는지 확인
if [ $? -eq 0 ]; then
    echo "Backup completed successfully: ${SQL_FILE}"
else
    echo "Backup failed"
fi
