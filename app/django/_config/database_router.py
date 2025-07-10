import random
from django.conf import settings


class MasterSlaveRouter:
    @staticmethod
    def db_for_read(model, **hints):
        # 슬레이브 DB 목록을 settings에서 가져옴
        slaves = getattr(settings, 'SLAVE_DATABASES', [])
        if slaves:
            return random.choice(slaves)
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
