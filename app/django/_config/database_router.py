import random
import sys

from django.conf import settings
from django.db import connections


class MasterSlaveRouter:
    @staticmethod
    def db_for_read(model, **hints):
        if 'migrate' in sys.argv:  # 마이그레이션 중에는 default 사용
            return 'default'
        slaves = getattr(settings, 'SLAVE_DATABASES', [])
        if not slaves:
            return 'default'
        try:
            slave = random.choice(slaves)
            if connections[slave].connection.is_usable():
                return slave
            return 'default'
        except Exception:
            return 'default'

    @staticmethod
    def db_for_write(model, **hints):
        # 쓰기 작업은 default 데이터베이스에서만 처리
        return 'default'

    @staticmethod
    def allow_relation(obj1, obj2, **hints):
        db_list = ['default'] + getattr(settings, 'SLAVE_DATABASES', [])
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    @staticmethod
    def allow_migrate(db, app_label, model_name=None, **hints):
        # default 데이터베이스에서만 마이그레이션 수행
        return db == 'default'
