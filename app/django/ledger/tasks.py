import logging
import os
import tempfile

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.db import transaction

from .models import (
    CompanyAccount, ProjectAccount,
    CompanyBankTransaction, ProjectBankTransaction,
    CompanyAccountingEntry, ProjectAccountingEntry
)
from .resources import (
    CompanyAccountResource, ProjectAccountResource,
    CompanyBankTransactionResource, ProjectBankTransactionResource,
    CompanyAccountingEntryResource, ProjectAccountingEntryResource
)

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
def async_import_ledger_account(self, file_path: str, user_id: int, resource_type: str = 'company_account') -> dict:
    """
    Ledger 관련 데이터를 비동기로 가져오기

    Args:
        file_path: 업로드된 파일 경로
        user_id: 사용자 ID
        resource_type: 리소스 타입
            - 'company_account': 본사 계정 과목
            - 'project_account': 프로젝트 계정 과목
            - 'company_bank_transaction': 본사 은행 거래
            - 'project_bank_transaction': 프로젝트 은행 거래
            - 'company_accounting_entry': 본사 회계 분개
            - 'project_accounting_entry': 프로젝트 회계 분개

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
        resource_mapping = {
            'company_account': (CompanyAccountResource, 'CompanyAccount'),
            'project_account': (ProjectAccountResource, 'ProjectAccount'),
            'company_bank_transaction': (CompanyBankTransactionResource, 'CompanyBankTransaction'),
            'project_bank_transaction': (ProjectBankTransactionResource, 'ProjectBankTransaction'),
            'company_accounting_entry': (CompanyAccountingEntryResource, 'CompanyAccountingEntry'),
            'project_accounting_entry': (ProjectAccountingEntryResource, 'ProjectAccountingEntry'),
        }

        if resource_type not in resource_mapping:
            raise ValueError(f"Unknown resource_type: {resource_type}")

        resource_class, model_name = resource_mapping[resource_type]

        # 데이터 가져오기 실행
        resource = resource_class()

        with open(tmp_file_path, 'rb') as file:
            from tablib import Dataset
            dataset = Dataset()
            dataset.load(file.read(), format='xlsx')

            # Clean empty rows from the dataset
            cleaned_dataset = Dataset(headers=dataset.headers)
            for row in dataset:
                if any(field is not None and str(field).strip() != '' for field in row):
                    cleaned_dataset.append(row)
            dataset = cleaned_dataset

            # 1. Dry run to validate data first
            dry_run_result = resource.import_data(dataset, dry_run=True, raise_errors=False)

            if dry_run_result.has_validation_errors():
                # If validation errors are found, do not import. Return errors.
                errors = [str(e.error) for e in dry_run_result.base_errors] + \
                         [f"Row {num} (Data: {row_data}): {', '.join([str(e) for e in errs])}"
                          for num, row_data, errs in dry_run_result.row_errors()]
                import_result = {
                    'success': False,
                    'model': model_name,
                    'total_rows': len(dataset),
                    'new_records': 0,
                    'updated_records': 0,
                    'skipped_records': len(dataset),
                    'error_count': len(dry_run_result.base_errors) + len(dry_run_result.row_errors()),
                    'errors': errors,
                    'user_email': user.email,
                }
                logger.warning(f"Import validation failed for user {user.username}: {errors}")
                # Send failure email if needed, then return
                if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
                    send_import_error_email(user.email, f"Validation failed. Errors: {errors[:5]}")
                return import_result

            # 2. If dry run is successful, proceed with actual import
            with transaction.atomic():
                result = resource.import_data(dataset, dry_run=False, raise_errors=True)  # raise_errors=True for safety

        # This part is now for a guaranteed successful import
        import_result = {
            'success': True,
            'model': model_name,
            'total_rows': len(dataset),
            'new_records': result.totals.get('new', 0),
            'updated_records': result.totals.get('update', 0),
            'skipped_records': result.totals.get('skip', 0),
            'error_count': 0,
            'errors': [],
            'user_email': user.email,
        }

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
            logger.warning(
                f"Retrying import task in {countdown} seconds (attempt {self.request.retries + 1}/{self.max_retries})")
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
def async_export_ledger_account(self, queryset_ids: list, user_id: int, resource_type: str = 'company_account') -> dict:
    """
    Ledger 관련 데이터를 비동기로 내보내기

    Args:
        queryset_ids: 내보낼 객체의 ID 목록
        user_id: 사용자 ID
        resource_type: 리소스 타입
            - 'company_account': 본사 계정 과목
            - 'project_account': 프로젝트 계정 과목
            - 'company_bank_transaction': 본사 은행 거래
            - 'project_bank_transaction': 프로젝트 은행 거래
            - 'company_accounting_entry': 본사 회계 분개
            - 'project_accounting_entry': 프로젝트 회계 분개

    Returns:
        dict: 내보내기 결과
    """
    try:
        user = User.objects.get(id=user_id)

        # 리소스 클래스 및 모델 선택
        resource_model_mapping = {
            'company_account': (CompanyAccountResource, CompanyAccount, 'CompanyAccount'),
            'project_account': (ProjectAccountResource, ProjectAccount, 'ProjectAccount'),
            'company_bank_transaction': (CompanyBankTransactionResource, CompanyBankTransaction,
                                         'CompanyBankTransaction'),
            'project_bank_transaction': (ProjectBankTransactionResource, ProjectBankTransaction,
                                         'ProjectBankTransaction'),
            'company_accounting_entry': (CompanyAccountingEntryResource, CompanyAccountingEntry,
                                         'CompanyAccountingEntry'),
            'project_accounting_entry': (ProjectAccountingEntryResource, ProjectAccountingEntry,
                                         'ProjectAccountingEntry'),
        }

        if resource_type not in resource_model_mapping:
            raise ValueError(f"Unknown resource_type: {resource_type}")

        resource_class, model_class, model_name = resource_model_mapping[resource_type]

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
