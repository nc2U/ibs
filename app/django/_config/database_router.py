import random


class MasterSlaveRouter:
    @staticmethod
    def db_for_read(model, **hints):
        # 읽기 작업은 slave1 또는 slave2에서 처리
        return random.choice(['slave1', 'slave2'])

    @staticmethod
    def db_for_write(model, **hints):
        # 쓰기 작업은 default 데이터베이스에서만 처리
        return 'default'

    @staticmethod
    def allow_relation(obj1, obj2, **hints):
        # 두 객체가 동일한 DB에 있을 때 관계 허용
        db_list = ('default', 'slave1', 'slave2')
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    @staticmethod
    def allow_migrate(db, app_label, model_name=None, **hints):
        # default 데이터베이스에서만 마이그레이션 수행
        return db == 'default'
