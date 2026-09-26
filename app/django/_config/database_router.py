import os
import time
from django.db import connections
from django.db.utils import OperationalError


class MasterSlaveRouter:
    CHECK_INTERVAL = 60  # 초 단위 재확인 주기

    def __init__(self):
        self._replica_enabled = False
        self._last_checked = 0
        self._is_k8s = 'KUBERNETES_SERVICE_HOST' in os.environ

    def _check_replica_available(self):
        """replica 데이터베이스 연결 가능 여부 주기적 확인 (TTL 60초)"""
        # Kubernetes 환경이 아니면 replica 사용 안함
        if not self._is_k8s:
            return False

        now = time.time()
        # 캐시 TTL이 유효하면 기존 상태 즉시 반환
        if (now - self._last_checked) < self.CHECK_INTERVAL:
            return self._replica_enabled

        self._last_checked = now
        try:
            if 'replica' not in connections:
                self._replica_enabled = False
                return False
            connection = connections['replica']
            connection.ensure_connection()
            self._replica_enabled = True
        except (OperationalError, KeyError, Exception):
            # replica 연결 실패 시 default 사용으로 안전하게 폴백
            self._replica_enabled = False

        return self._replica_enabled

    def db_for_read(self, model, **hints):
        return 'replica' if self._check_replica_available() else 'default'

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
