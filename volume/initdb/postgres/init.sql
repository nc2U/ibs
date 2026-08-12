-- template1 템플릿 DB에 확장 생성 (Django test_ibs 테스트 DB 자동 상속용)
\connect template1
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- ibs 메인 DB로 복귀
\connect ibs

-- schema만 생성 (user, db, 권한은 이미 있음)
CREATE SCHEMA IF NOT EXISTS ibs AUTHORIZATION ibs;

-- search_path 설정
ALTER DATABASE ibs SET search_path TO ibs, public;

-- pg_trgm 확장 활성화 (Work 앱 통합검색 GIN 인덱스용)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;