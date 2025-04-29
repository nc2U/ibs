#!/bin/bash
# /docker-entrypoint-initdb.d/initdb.sh
initdb --encoding=UTF8 --locale=en_US.UTF-8
SET timezone TO 'Asia/Seoul';