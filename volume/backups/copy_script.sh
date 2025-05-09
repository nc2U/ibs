#!/bin/bash
# 스크립트 파일이 위치한 디렉터리 경로
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DATE=$(date +"%Y-%m-%d")
# 디렉토리 존재 여부 확인 및 없으면 생성
DEST_DIR=/volume1/mnt/ibs/dev/volume/backups/
if [ ! -d "${DEST_DIR}" ]; then
    mkdir -p "${DEST_DIR}"
fi

MARIADB_BACKUP_FILE="${SCRIPT_DIR}/bu-mariadb-${DATE}.sql"  # 스크립트 디렉터리를 기준으로 파일 경로 설정
# 파일 존재 여부 확인
if [ -f "${MARIADB_BACKUP_FILE}" ]; then
    # 파일 복사
    cp "${MARIADB_BACKUP_FILE}" "${DEST_DIR}"
    echo "File ${MARIADB_BACKUP_FILE} copied to ${DEST_DIR}"
else
    echo "File ${MARIADB_BACKUP_FILE} does not exist."
fi

POSTGRES_BACKUP_FILE="${SCRIPT_DIR}/bu-postgres-${DATE}.dump"  # 스크립트 디렉터리를 기준으로 파일 경로 설정
# 파일 존재 여부 확인
if [ -f "${POSTGRES_BACKUP_FILE}" ]; then
    # 파일 복사
    cp "${POSTGRES_BACKUP_FILE}" "${DEST_DIR}"
    echo "File ${POSTGRES_BACKUP_FILE} copied to ${DEST_DIR}"
else
    echo "File ${POSTGRES_BACKUP_FILE} does not exist."
fi