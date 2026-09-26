import re
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.utils.html import strip_tags


def _render_template(template_text: str, context: dict) -> str:
    """템플릿 내 {{ 변수 }} 치환"""
    result = template_text
    for key, value in context.items():
        # {{ key }} 형태 치환
        pattern = re.compile(rf'\{{\{{\s*{re.escape(key)}\s*\}}\}}', re.IGNORECASE)
        result = pattern.sub(str(value or ''), result)
    return result


@shared_task(bind=True, max_retries=1)
def send_mass_email_task(self, email_notice_id: int):
    """
    대량 계약자 이메일 비동기 발송 태스크.
    각 계약자별 로그 레코드를 조회하여 개별 치환 후 전송.
    """
    from notice.models import EmailNotice, EmailSendLog

    try:
        notice = EmailNotice.objects.select_related('project').get(pk=email_notice_id)
    except EmailNotice.DoesNotExist:
        return {'status': 'error', 'message': f'EmailNotice {email_notice_id} not found.'}

    notice.status = 'sending'
    notice.save(update_fields=['status'])

    logs = notice.send_logs.filter(status='pending').select_related('contractor')
    success_count = notice.success_count
    fail_count = notice.fail_count

    from email.utils import parseaddr, formataddr

    raw_default = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@ibs.local')
    default_name, default_addr = parseaddr(raw_default)
    actual_addr = notice.sender_email.strip() or default_addr or raw_default
    actual_name = notice.sender_name.strip() or default_name

    from_email = formataddr((actual_name, actual_addr)) if actual_name else actual_addr

    project_name = notice.project.name if notice.project else ''

    from django.core.mail import get_connection

    connection = get_connection()
    try:
        connection.open()
    except Exception:
        connection = None

    try:
        for log in logs:
            context = {
                '계약자명': log.recipient_name,
                'name': log.recipient_name,
                '동호수': log.unit_info,
                'unit': log.unit_info,
                '프로젝트명': project_name,
                'project': project_name,
            }

            rendered_title = _render_template(notice.title, context)
            rendered_html = _render_template(notice.content, context)
            text_content = strip_tags(rendered_html)

            try:
                msg = EmailMultiAlternatives(
                    subject=rendered_title,
                    body=text_content,
                    from_email=from_email,
                    to=[log.recipient_email],
                    connection=connection,
                )
                msg.attach_alternative(rendered_html, 'text/html')
                msg.send(fail_silently=False)

                log.status = 'success'
                log.sent_at = timezone.now()
                log.save(update_fields=['status', 'sent_at'])
                success_count += 1
            except Exception as exc:
                log.status = 'fail'
                log.error_message = str(exc)
                log.sent_at = timezone.now()
                log.save(update_fields=['status', 'error_message', 'sent_at'])
                fail_count += 1
    finally:
        if connection:
            try:
                connection.close()
            except Exception:
                pass

    success_count = notice.send_logs.filter(status='success').count()
    fail_count = notice.send_logs.filter(status='fail').count()
    notice.success_count = success_count
    notice.fail_count = fail_count
    notice.status = 'completed' if fail_count == 0 else ('failed' if success_count == 0 and fail_count > 0 else 'completed')
    notice.completed_at = timezone.now()
    notice.save(update_fields=['success_count', 'fail_count', 'status', 'completed_at'])

    return {
        'notice_id': email_notice_id,
        'success': success_count,
        'fail': fail_count,
    }
