from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from _utils.push_service import send_push_notification


@shared_task
def notify_approvers_task(document_pk, step_pk):
    """결재 요청 알림: 다음 결재 단계 결재자들에게 푸시 + 인앱 알림 발송"""
    from approval.models import ApprovalDocument, ApprovalStep
    try:
        document = ApprovalDocument.objects.select_related('doc_type', 'drafter__profile').get(pk=document_pk)
        step = ApprovalStep.objects.prefetch_related('approvers').get(pk=step_pk)
        approver_ids = list(step.approvers.values_list('id', flat=True))

        push_title = f'[결재 요청] {document.doc_type.name}'
        profile = getattr(document.drafter, 'profile', None)
        drafter_name = profile.name if profile and profile.name else document.drafter.username
        push_body = f'{drafter_name}님이 결재를 요청했습니다: {document.title}'

        send_push_notification(
            user_ids=approver_ids,
            title=push_title,
            body=push_body,
            category='approval',
            target_type='approval_document',
            target_id=str(document_pk),
        )
    except Exception as e:
        print(f'❌ notify_approvers_task failed: {e}')


@shared_task
def notify_drafter_task(document_pk, action, comment=''):
    """결재 완료/반려 알림: 기안자 및 참조자에게 결과 푸시 + 인앱 알림 발송"""
    from approval.models import ApprovalDocument
    try:
        document = ApprovalDocument.objects.select_related('doc_type', 'drafter').prefetch_related('observers').get(pk=document_pk)

        if action == 'approved':
            push_title = f'[결재 완료] {document.doc_type.name}'
            push_body = f'"{document.title}" 결재가 최종 승인되었습니다.'
        elif action == 'rejected':
            push_title = f'[결재 반려] {document.doc_type.name}'
            push_body = f'"{document.title}" 결재가 반려되었습니다.' + (f' 사유: {comment}' if comment else '')
        elif action == 'commented':
            push_title = f'[결재 의견 등록] {document.doc_type.name}'
            push_body = f'"{document.title}" 결재에 새로운 의견이 등록되었습니다.' + (f': {comment}' if comment else '')
        else:
            return

        # 기안자 알림
        send_push_notification(
            user_ids=[document.drafter_id],
            title=push_title,
            body=push_body,
            category='approval',
            target_type='approval_document',
            target_id=str(document_pk),
        )

        # 최종 승인 시 참조자들에게 공람 알림 발송
        if action == 'approved':
            observer_ids = list(document.observers.exclude(id=document.drafter_id).values_list('id', flat=True))
            if observer_ids:
                obs_title = f'[결재 공람] {document.doc_type.name}'
                obs_body = f'"{document.title}" 결재가 최종 승인되어 공람되었습니다.'
                send_push_notification(
                    user_ids=observer_ids,
                    title=obs_title,
                    body=obs_body,
                    category='approval',
                    target_type='approval_document',
                    target_id=str(document_pk),
                )
    except Exception as e:
        print(f'❌ notify_drafter_task failed: {e}')


@shared_task
def generate_approval_pdf_task(document_pk):
    """결재 최종 승인 후 PDF 생성 및 스토리지 저장"""
    from approval.models import ApprovalDocument, ApprovalStep, ApprovalAction
    import io
    try:
        from weasyprint import HTML
    except ImportError:
        print('⚠️ WeasyPrint is not installed. PDF generation skipped.')
        return

    try:
        from django.template.loader import render_to_string
        document = ApprovalDocument.objects.select_related(
            'doc_type', 'drafter'
        ).prefetch_related(
            'steps__approvers', 'steps__actions__approver'
        ).get(pk=document_pk)

        html_string = render_to_string('approval/pdf_document.html', {
            'document': document,
            'steps': document.steps.all(),
            'settings': settings,
        })

        pdf_bytes = HTML(string=html_string, base_url=settings.DOMAIN_HOST).write_pdf()
        filename = f'approval/pdf/{document.doc_type.code}-{document_pk}.pdf'

        from django.core.files.base import ContentFile
        document.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)
        print(f'✅ PDF generated and saved: {filename}')
    except Exception as e:
        print(f'❌ generate_approval_pdf_task failed: {e}')
