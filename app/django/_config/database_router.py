import os
from django.db import connections
from django.db.utils import OperationalError


class MasterSlaveRouter:
    def __init__(self):
        self.replica_enabled = self._check_replica_available()

    @staticmethod
    def _check_replica_available():
        """replica 데이터베이스 연결 가능 여부 확인"""
        # Kubernetes 환경이 아니면 replica 사용 안함
        if 'KUBERNETES_SERVICE_HOST' not in os.environ:
            return False

        # replica 연결 가능 여부 확인 (캐싱됨)
        try:
            connection = connections['replica']
            connection.ensure_connection()
            return True
        except (OperationalError, KeyError):
            # replica 연결 실패 시 default 사용
            return False

    def db_for_read(self, model, **hints):
        return 'replica' if self.replica_enabled else 'default'

    @staticmethod
    def db_for_write(model, **hints):
        # 쓰기 작업은 default 데이터베이스에서만 처리
        return 'default'

    @staticmethod
    def allow_relation(obj1, obj2, **hints):
        db_list = ['default', 'replica']
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    @staticmethod
    def allow_migrate(db, app_label, model_name=None, **hints):
        # default 데이터베이스에서만 마이그레이션 수행
        return db == 'default'
