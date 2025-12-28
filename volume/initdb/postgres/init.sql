-- schema만 생성 (user, db, 권한은 이미 있음)
CREATE SCHEMA IF NOT EXISTS ibs AUTHORIZATION ibs;

-- search_path 설정 (선택)
ALTER DATABASE ibs SET search_path TO ibs, public;