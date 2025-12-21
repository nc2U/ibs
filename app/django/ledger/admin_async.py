from celery.result import AsyncResult
from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html
from import_export.admin import ImportExportMixin

from .models import (
    CompanyAccount, ProjectAccount,
    CompanyBankTransaction, ProjectBankTransaction,
    CompanyAccountingEntry, ProjectAccountingEntry,
    ImportJob
)
from .tasks import async_import_ledger_account, async_export_ledger_account


class AsyncImportExportMixin(ImportExportMixin):
    """
    ImportExportMixin을 확장하여 비동기 가져오기/내보내기 기능 추가
    """
    async_import_template = 'admin/ledger/async_import.html'
    async_status_template = 'admin/ledger/async_status.html'

    # 파일 크기 임계값 (바이트) - 1MB 이상의 파일을 비동기 처리
    async_threshold_size = 0.5 * 1024 * 1024  # 0.5MB

    def import_action(self, request, *args, **kwargs):
        """기존 import 버튼을 async-import로 리다이렉트"""
        return redirect('admin:%s_%s_async_import' % (
            self.model._meta.app_label,
            self.model._meta.model_name
        ))

    def get_urls(self):
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name

        custom_urls = [
            path('async-import/',
                 self.admin_site.admin_view(self.async_import_view),
                 name='%s_%s_async_import' % info),
            path('async-status/<int:job_id>/',
                 self.admin_site.admin_view(self.async_status_view),
                 name='%s_%s_async_status' % info),
            path('async-progress/<int:job_id>/',
                 self.admin_site.admin_view(self.async_progress_api),
                 name='%s_%s_async_progress' % info),
            path('async-export/',
                 self.admin_site.admin_view(self.async_export_view),
                 name='%s_%s_async_export' % info),
        ]
        return custom_urls + urls

    def async_import_view(self, request):
        """비동기 가져오기 페이지"""
        if not self.has_import_permission(request):
            raise PermissionDenied

        context = {
            'title': f'{self.model._meta.verbose_name} 비동기 가져오기',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
            'async_threshold_mb': self.async_threshold_size // (1024 * 1024),
        }

        if request.method == 'POST':
            if 'import_file' not in request.FILES:
                messages.error(request, '파일을 선택해주세요.')
                return TemplateResponse(request, self.async_import_template, context)

            import_file = request.FILES['import_file']

            # 파일 크기 확인
            if import_file.size > self.async_threshold_size:
                # 비동기 처리
                return self._handle_async_import(request, import_file)
            else:
                # 동기 처리 (기존 방식)
                messages.info(request, '파일 크기가 작아 일반 가져오기로 처리됩니다.')
                return redirect('admin:%s_%s_import' % (
                    self.model._meta.app_label,
                    self.model._meta.model_name
                ))

        return TemplateResponse(request, self.async_import_template, context)

    def _handle_async_import(self, request, import_file):
        """비동기 가져오기 처리"""
        # 모델에 따른 resource_type 매핑
        resource_type_mapping = {
            CompanyAccount: 'company_account',
            ProjectAccount: 'project_account',
            CompanyBankTransaction: 'company_bank_transaction',
            ProjectBankTransaction: 'project_bank_transaction',
            CompanyAccountingEntry: 'company_accounting_entry',
            ProjectAccountingEntry: 'project_accounting_entry',
        }
        resource_type = resource_type_mapping.get(self.model, 'unknown')

        job = ImportJob.objects.create(
            job_type='import',
            resource_type=resource_type,
            file=import_file,
            status=ImportJob.PENDING,
            creator=request.user
        )

        # 비동기 태스크 시작
        task = async_import_ledger_account.delay(
            file_path=job.file.name,
            user_id=request.user.id,
            resource_type=resource_type
        )

        job.task_id = task.id
        job.status = ImportJob.PROCESSING
        job.started_at = timezone.now()
        job.save()

        messages.success(
            request,
            f'비동기 가져오기가 시작되었습니다. 작업 ID: {job.id}'
        )

        return redirect('admin:%s_%s_async_status' % (
            self.model._meta.app_label,
            self.model._meta.model_name
        ), job_id=job.id)

    def async_status_view(self, request, job_id):
        """비동기 작업 상태 페이지"""
        job = get_object_or_404(ImportJob, id=job_id, creator=request.user)

        context = {
            'title': f'작업 상태: {job}',
            'job': job,
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }

        return TemplateResponse(request, self.async_status_template, context)

    @staticmethod
    def async_progress_api(request, job_id):
        """비동기 작업 진행률 API"""
        job = get_object_or_404(ImportJob, id=job_id, creator=request.user)

        # Celery 태스크 상태 확인
        if job.task_id:
            task_result = AsyncResult(job.task_id)

            if task_result.state == 'SUCCESS':
                result = task_result.result
                if result and result.get('success'):
                    job.status = ImportJob.COMPLETED
                    job.total_records = result.get('total_rows', 0)
                    job.processed_records = result.get('new_records', 0) + result.get('updated_records', 0)
                    job.success_count = job.processed_records
                    job.error_count = result.get('error_count', 0)
                    if result.get('errors'):
                        job.error_message = '\n'.join(result['errors'][:10])  # 처음 10개 오류만
                else:  # if not result or not result.get('success')
                    job.status = ImportJob.FAILED
                    job.error_count = result.get('error_count', 0)
                    job.error_message = '\n'.join(result.get('errors', [])[:10])  # Keep summary
                    job.error_details = result.get('row_errors')  # Save structured data
                job.completed_at = timezone.now()
                job.save()

            elif task_result.state == 'FAILURE':
                job.status = ImportJob.FAILED
                job.completed_at = timezone.now()
                job.error_message = str(task_result.result)
                job.save()

        return JsonResponse({
            'status': job.status,
            'progress': job.progress,
            'processed': job.processed_records,
            'total': job.total_records,
            'success_count': job.success_count,
            'error_count': job.error_count,
            'error_message': job.error_message,
            'completed': job.status in [ImportJob.COMPLETED, ImportJob.FAILED],
            'duration': str(job.duration) if job.duration else None,
        })

    def async_export_view(self, request):
        """비동기 내보내기 처리"""
        if not self.has_export_permission(request):
            raise PermissionDenied

        # 선택된 객체들의 ID 가져오기
        selected_ids = request.GET.getlist('ids')
        if not selected_ids:
            messages.error(request, '내보낼 항목을 선택해주세요.')
            return redirect('admin:%s_%s_changelist' % (
                self.model._meta.app_label,
                self.model._meta.model_name
            ))

        # 대용량 내보내기인지 확인 (1000개 이상)
        if len(selected_ids) >= 1000:
            # 모델에 따른 resource_type 매핑
            resource_type_mapping = {
                CompanyAccount: 'company_account',
                ProjectAccount: 'project_account',
                CompanyBankTransaction: 'company_bank_transaction',
                ProjectBankTransaction: 'project_bank_transaction',
                CompanyAccountingEntry: 'company_accounting_entry',
                ProjectAccountingEntry: 'project_accounting_entry',
            }
            resource_type = resource_type_mapping.get(self.model, 'unknown')

            job = ImportJob.objects.create(
                job_type='export',
                resource_type=resource_type,
                status=ImportJob.PENDING,
                creator=request.user,
                total_records=len(selected_ids)
            )

            task = async_export_ledger_account.delay(
                queryset_ids=[int(id) for id in selected_ids],
                user_id=request.user.id,
                resource_type=resource_type
            )

            job.task_id = task.id
            job.status = ImportJob.PROCESSING
            job.started_at = timezone.now()
            job.save()

            messages.success(
                request,
                f'비동기 내보내기가 시작되었습니다. 작업 ID: {job.id}'
            )

            return redirect('admin:%s_%s_async_status' % (
                self.model._meta.app_label,
                self.model._meta.model_name
            ), job_id=job.id)
        else:
            # 일반 내보내기로 리다이렉트
            return redirect('admin:%s_%s_export' % (
                self.model._meta.app_label,
                self.model._meta.model_name
            ))


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    """가져오기/내보내기 작업 관리"""
    list_display = ('id', 'job_type', 'resource_type', 'status', 'progress_bar',
                    'success_count', 'error_count', 'creator', 'created_at', 'duration_display')
    list_filter = ('job_type', 'resource_type', 'status', 'created_at')
    search_fields = ('task_id', 'creator__username', 'error_message')
    readonly_fields = ('task_id', 'created_at', 'started_at', 'completed_at', 'duration_display')

    def progress_bar(self, obj):
        """진행률 표시"""
        if obj.total_records > 0:
            percentage = (obj.processed_records / obj.total_records) * 100
            color = 'green' if obj.status == ImportJob.COMPLETED else 'blue' if obj.status == ImportJob.PROCESSING else 'red'
            return format_html(
                '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
                '<div style="width: {}px; height: 20px; background-color: {}; border-radius: 3px; text-align: center; line-height: 20px; color: white; font-size: 12px;">'
                '{}%</div></div>',
                int(percentage), color, int(percentage)
            )
        return '-'

    progress_bar.short_description = '진행률'

    def duration_display(self, obj):
        """작업 소요 시간 표시"""
        duration = obj.duration
        if duration:
            total_seconds = int(duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours:
                return f'{hours}시간 {minutes}분 {seconds}초'
            elif minutes:
                return f'{minutes}분 {seconds}초'
            else:
                return f'{seconds}초'
        return '-'

    duration_display.short_description = '소요 시간'
