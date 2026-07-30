from django.db import migrations, models
from decouple import config


def populate_slack_webhook_urls(apps, schema_editor):
    """
    기존 .env 환경변수(SLACK_COMPANY_URL, SLACK_PROJECT_***)에 등록된 슬랙 웹훅 URL을
    IssueProject DB 테이블의 slack_webhook_url 컬럼으로 자동 이관하는 데이터 마이그레이션
    """
    IssueProject = apps.get_model('work', 'IssueProject')

    for project in IssueProject.objects.all():
        webhook_url = None
        if project.type == '1':  # 본사관리
            webhook_url = config('SLACK_COMPANY_URL', default=None)
        else:  # 개별 현장 프로젝트
            key = f"SLACK_PROJECT_{project.slug.replace('-', '_').upper()}"
            webhook_url = config(key, default=None)

        if webhook_url and webhook_url.strip():
            project.slack_webhook_url = webhook_url.strip()
            project.save(update_fields=['slack_webhook_url'])


def reverse_populate(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('work', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='issueproject',
            name='slack_webhook_url',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Slack Incoming Webhook URL (미입력 시 본사/기본 알림 URL을 사용합니다).',
                max_length=255,
                verbose_name='Slack Webhook URL'
            ),
        ),
        migrations.AlterField(
            model_name='issueproject',
            name='slack_notifications_enabled',
            field=models.BooleanField(
                default=False,
                help_text='이 프로젝트의 데이터 변동을 Slack으로 실시간 알림받습니다.',
                verbose_name='Slack 알림 활성화'
            ),
        ),
        migrations.RunPython(populate_slack_webhook_urls, reverse_code=reverse_populate),
    ]
