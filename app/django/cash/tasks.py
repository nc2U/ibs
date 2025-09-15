import os
import tempfile
from typing import Optional
from celery import shared_task
from celery.exceptions import Retry
from django.core.files.storage import default_storage
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
import logging

from .models import CashBook, ProjectCashBook
from .resources import CashBookResource, ProjectCashBookResource

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,  # 5분 최대 지연
    max_retries=3,
    retry_jitter=True
)
def async_import_cashbook(self, file_path: str, user_id: int, resource_type: str = 'cashbook') -> dict:
    """
    CashBook 또는 ProjectCashBook 데이터를 비동기로 가져오기
    
    Args:
        file_path: 업로드된 파일 경로
        user_id: 사용자 ID
        resource_type: 'cashbook' 또는 'project_cashbook'
    
    Returns:
        dict: 가져오기 결과
    """
    tmp_file_path = None
    
    try:
        # 사용자 정보 가져오기
        user = User.objects.get(id=user_id)
        
        # 임시 파일로 다운로드
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            with default_storage.open(file_path, 'rb') as uploaded_file:
                tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name
        
        # 리소스 클래스 선택
        if resource_type == 'project_cashbook':
            resource_class = ProjectCashBookResource
            model_name = 'ProjectCashBook'
        else:
            resource_class = CashBookResource
            model_name = 'CashBook'
        
        # 데이터 가져오기 실행
        resource = resource_class()
        
        with open(tmp_file_path, 'rb') as file:
            from tablib import Dataset
            dataset = Dataset()
            dataset.load(file.read(), format='xlsx')
            
            # 트랜잭션 내에서 가져오기 실행
            with transaction.atomic():
                result = resource.import_data(dataset, dry_run=False, raise_errors=False)
        
        # 결과 정리
        import_result = {
            'success': True,
            'model': model_name,
            'total_rows': len(dataset),
            'new_records': result.totals.get('new', 0),
            'updated_records': result.totals.get('update', 0),
            'skipped_records': result.totals.get('skip', 0),
            'error_count': len(result.base_errors) + len(result.row_errors),
            'errors': [str(error.error) for error in result.base_errors + result.row_errors],
            'user_email': user.email,
        }

        # Slack 요약 알림 발송
        from _utils.slack_notifications import send_bulk_import_summary
        summary_data = {
            'model_name': model_name,
            'total_records': result.totals.get('new', 0) + result.totals.get('update', 0),
            'new_records': result.totals.get('new', 0),
            'updated_records': result.totals.get('update', 0),
            'skipped_records': result.totals.get('skip', 0),
            'error_count': len(result.base_errors) + len(result.row_errors)
        }
        send_bulk_import_summary(summary_data, user)

        # 성공 이메일 발송
        if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
            send_import_success_email(user.email, import_result)

        logger.info(f"Import completed successfully for user {user.username}: {import_result}")
        return import_result
        
    except Exception as e:
        error_msg = f"Import failed for user {user_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 오류 이메일 발송
        try:
            user = User.objects.get(id=user_id)
            if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
                send_import_error_email(user.email, error_msg)
        except:
            pass
        
        # Celery 재시도 로직
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries  # 지수 백오프
            logger.warning(f"Retrying import task in {countdown} seconds (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=countdown)
        
        return {
            'success': False,
            'error': str(e),
            'user_id': user_id,
            'file_path': file_path
        }
        
    finally:
        # 임시 파일 정리
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except OSError:
                logger.warning(f"Failed to delete temporary file: {tmp_file_path}")


@shared_task(bind=True)
def async_export_cashbook(self, queryset_ids: list, user_id: int, resource_type: str = 'cashbook') -> dict:
    """
    CashBook 또는 ProjectCashBook 데이터를 비동기로 내보내기
    
    Args:
        queryset_ids: 내보낼 객체의 ID 목록
        user_id: 사용자 ID
        resource_type: 'cashbook' 또는 'project_cashbook'
    
    Returns:
        dict: 내보내기 결과
    """
    try:
        user = User.objects.get(id=user_id)
        
        # 리소스 클래스 선택
        if resource_type == 'project_cashbook':
            resource_class = ProjectCashBookResource
            model_class = ProjectCashBook
            model_name = 'ProjectCashBook'
        else:
            resource_class = CashBookResource
            model_class = CashBook
            model_name = 'CashBook'
        
        # 쿼리셋 생성
        queryset = model_class.objects.filter(id__in=queryset_ids)
        
        # 데이터 내보내기
        resource = resource_class()
        dataset = resource.export(queryset)
        
        # 파일로 저장
        file_format = 'xlsx'
        export_data = dataset.export(file_format)
        
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_format}', mode='wb') as tmp_file:
            tmp_file.write(export_data)
            tmp_file_path = tmp_file.name
        
        # 스토리지에 업로드
        with open(tmp_file_path, 'rb') as file:
            file_name = f'exports/{model_name.lower()}_{user_id}_{self.request.id}.{file_format}'
            saved_path = default_storage.save(file_name, file)
        
        # 임시 파일 삭제
        os.unlink(tmp_file_path)
        
        export_result = {
            'success': True,
            'model': model_name,
            'file_path': saved_path,
            'file_url': default_storage.url(saved_path) if hasattr(default_storage, 'url') else None,
            'record_count': len(queryset),
            'user_email': user.email,
        }
        
        # 성공 이메일 발송
        if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
            send_export_success_email(user.email, export_result)
        
        logger.info(f"Export completed successfully for user {user.username}: {export_result}")
        return export_result
        
    except Exception as e:
        error_msg = f"Export failed for user {user_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        try:
            user = User.objects.get(id=user_id)
            if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
                send_export_error_email(user.email, error_msg)
        except:
            pass
        
        return {
            'success': False,
            'error': str(e),
            'user_id': user_id
        }


def send_import_success_email(user_email: str, result: dict):
    """가져오기 성공 이메일 발송"""
    subject = f"[IBS] {result['model']} 데이터 가져오기 완료"
    message = f"""
안녕하세요,

{result['model']} 데이터 가져오기가 성공적으로 완료되었습니다.

처리 결과:
- 전체 행: {result['total_rows']}
- 새로 생성: {result['new_records']}
- 업데이트: {result['updated_records']}
- 건너뜀: {result['skipped_records']}
- 오류: {result['error_count']}

{f"오류 내용: {', '.join(result['errors'][:5])}" if result['errors'] else ""}

감사합니다.
IBS 시스템
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=True
    )


def send_import_error_email(user_email: str, error_msg: str):
    """가져오기 오류 이메일 발송"""
    subject = "[IBS] 데이터 가져오기 오류 발생"
    message = f"""
안녕하세요,

데이터 가져오기 중 오류가 발생했습니다.

오류 내용: {error_msg}

관리자에게 문의하시기 바랍니다.

감사합니다.
IBS 시스템
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=True
    )


def send_export_success_email(user_email: str, result: dict):
    """내보내기 성공 이메일 발송"""
    subject = f"[IBS] {result['model']} 데이터 내보내기 완료"
    message = f"""
안녕하세요,

{result['model']} 데이터 내보내기가 성공적으로 완료되었습니다.

처리 결과:
- 내보낸 레코드: {result['record_count']}개
- 파일 경로: {result['file_path']}
{f"- 다운로드 링크: {result['file_url']}" if result['file_url'] else ""}

감사합니다.
IBS 시스템
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=True
    )


def send_export_error_email(user_email: str, error_msg: str):
    """내보내기 오류 이메일 발송"""
    subject = "[IBS] 데이터 내보내기 오류 발생"
    message = f"""
안녕하세요,

데이터 내보내기 중 오류가 발생했습니다.

오류 내용: {error_msg}

관리자에게 문의하시기 바랍니다.

감사합니다.
IBS 시스템
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=True
    )