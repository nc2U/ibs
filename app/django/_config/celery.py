import os
from celery import Celery

# Django 설정 모듈 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_config.settings')

app = Celery('ibs')

# Django 설정에서 Celery 구성 로드
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django 앱에서 task 자동 탐색
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')