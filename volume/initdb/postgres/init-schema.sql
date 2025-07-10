-- 1. ibs 스키마가 없으면 생성
CREATE SCHEMA IF NOT EXISTS ibs;

-- 2. ibs 유저에게 ibs 스키마 권한 부여
GRANT ALL ON SCHEMA ibs TO ibs;

-- 3. 해당 데이터베이스의 기본 검색 경로를 ibs → public 순서로 설정
ALTER DATABASE ibs SET search_path TO ibs, public;