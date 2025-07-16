import os


class MasterSlaveRouter:
    def __init__(self):
        self.replica_enabled = 'KUBERNETES_SERVICE_HOST' in os.environ

    def db_for_read(self, model, **hints):
        return 'default'  # 'replica' if self.replica_enabled else 'default'

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
