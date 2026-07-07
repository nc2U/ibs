from django.apps import AppConfig


class ForumConfig(AppConfig):
    name = 'forum'
    verbose_name = '*** 게시판 관리 [forum]'

    def ready(self):
        import forum.signals
