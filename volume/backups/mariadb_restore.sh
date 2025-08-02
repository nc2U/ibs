#!/bin/bash
DATE=$(date +"%Y-%m-%d")
SQL_FILE="/var/backups/ibs-backup-mariadb-${DATE}.sql"

# shellcheck disable=SC2046
find /var/backups \( -name "*.sql" -o -name "*.log" \) -type f -ctime +2 -delete

mariadb -u"${USER}" -p"${PASSWORD}" "${DATABASE}" < "${SQL_FILE}"

# 복원 성공 여부 확인
if [ $? -eq 0 ]; then
    echo "MARIADB Database restoration completed successfully: ${SQL_FILE}"
else
    echo "MARIADB Database restoration failed"
fi
