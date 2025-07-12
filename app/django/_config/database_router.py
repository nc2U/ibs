import os


class MasterSlaveRouter:
    def __init__(self):
        self.replica_enabled = os.getenv('REPLICA_ENABLED', 'false').lower() == 'true'

    def db_for_read(self, model, **hints):
        if self.replica_enabled:
            return 'replica'
        return 'default'

    @staticmethod
    def db_for_write(model, **hints):
        # 쓰기 작업은 default 데이터베이스에서만 처리
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._state.db == obj2._state.db:  # 두 객체가 모두 같은 DB에 있다면 관계 허용
            return True
        if not self.replica_enabled:  # 레플리카가 없을 때 관계 허용
            return True
        return False

    @staticmethod
    def allow_migrate(db, app_label, model_name=None, **hints):
        # default 데이터베이스에서만 마이그레이션 수행
        return db == 'default'
