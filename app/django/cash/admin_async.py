from django.contrib import admin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import path, reverse
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.admin import helpers
from django.contrib.admin.utils import unquote
from django.utils.html import format_html
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db import models
from django.template.response import TemplateResponse
from import_export.admin import ImportExportMixin
from django.contrib.humanize.templatetags.humanize import intcomma

from .models import CashBook, ProjectCashBook, ImportJob
from .tasks import async_import_cashbook, async_export_cashbook
from .resources import CashBookResource, ProjectCashBookResource


class AsyncImportExportMixin(ImportExportMixin):
    """
    ImportExportMixin을 확장하여 비동기 가져오기/내보내기 기능 추가
    """
    async_import_template = 'admin/cash/async_import.html'
    async_status_template = 'admin/cash/async_status.html'
    
    # 파일 크기 임계값 (바이트) - 5MB 이상이면 비동기 처리
    async_threshold_size = 5 * 1024 * 1024
    
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
        # ImportJob 생성
        resource_type = 'project_cashbook' if self.model == ProjectCashBook else 'cashbook'
        
        job = ImportJob.objects.create(
            job_type='import',
            resource_type=resource_type,
            file=import_file,
            status=ImportJob.PENDING,
            creator=request.user
        )
        
        # 비동기 태스크 시작
        task = async_import_cashbook.delay(
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
    
    def async_progress_api(self, request, job_id):
        """비동기 작업 진행률 API"""
        job = get_object_or_404(ImportJob, id=job_id, creator=request.user)
        
        # Celery 태스크 상태 확인
        if job.task_id:
            from celery.result import AsyncResult
            task_result = AsyncResult(job.task_id)
            
            if task_result.state == 'SUCCESS':
                job.status = ImportJob.COMPLETED
                job.completed_at = timezone.now()
                
                # 태스크 결과에서 상세 정보 업데이트
                result = task_result.result
                if result and result.get('success'):
                    job.total_records = result.get('total_rows', 0)
                    job.processed_records = result.get('new_records', 0) + result.get('updated_records', 0)
                    job.success_count = job.processed_records
                    job.error_count = result.get('error_count', 0)
                    if result.get('errors'):
                        job.error_message = '\n'.join(result['errors'][:10])  # 처음 10개 오류만
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
            # 비동기 처리
            resource_type = 'project_cashbook' if self.model == ProjectCashBook else 'cashbook'
            
            job = ImportJob.objects.create(
                job_type='export',
                resource_type=resource_type,
                status=ImportJob.PENDING,
                creator=request.user,
                total_records=len(selected_ids)
            )
            
            task = async_export_cashbook.delay(
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


class AsyncCashBookAdmin(AsyncImportExportMixin, admin.ModelAdmin):
    """
    비동기 가져오기/내보내기 기능이 추가된 CashBook Admin
    """
    resource_classes = [CashBookResource]
    list_display = ('id', 'deal_date', 'sort', 'account_d1', 'account_d2', 'account_d3', 'content',
                    'trader', 'bank_account', 'formatted_income', 'formatted_outlay', 'evidence', 'creator')
    list_editable = ('account_d1', 'account_d2', 'account_d3', 'content', 'trader', 'evidence')
    search_fields = ('account_d3', 'content', 'trader', 'note')
    list_display_links = ('deal_date', 'sort', 'bank_account')
    list_filter = ('company', ('deal_date', 'rangefilter.filters.DateRangeFilter'), 'sort',
                   'account_d1', 'account_d2', 'account_d3', 'evidence')
    
    actions = ['async_export_selected']
    
    def formatted_income(self, obj):
        return f'{intcomma(obj.income)} 원' if obj.income else '-'
    
    def formatted_outlay(self, obj):
        return f'{intcomma(obj.outlay)} 원' if obj.outlay else '-'
    
    formatted_income.short_description = '입금액'
    formatted_outlay.short_description = '출금액'
    
    def async_export_selected(self, request, queryset):
        """선택된 항목을 비동기로 내보내기"""
        selected_ids = list(queryset.values_list('id', flat=True))
        
        if len(selected_ids) >= 1000:
            # 비동기 처리
            job = ImportJob.objects.create(
                job_type='export',
                resource_type='cashbook',
                status=ImportJob.PENDING,
                creator=request.user,
                total_records=len(selected_ids)
            )
            
            task = async_export_cashbook.delay(
                queryset_ids=selected_ids,
                user_id=request.user.id,
                resource_type='cashbook'
            )
            
            job.task_id = task.id
            job.status = ImportJob.PROCESSING
            job.started_at = timezone.now()
            job.save()
            
            self.message_user(
                request,
                f'{len(selected_ids)}개 항목의 비동기 내보내기가 시작되었습니다. (작업 ID: {job.id})',
                messages.SUCCESS
            )
            
            return HttpResponseRedirect(
                reverse('admin:cash_cashbook_async_status', args=[job.id])
            )
        else:
            # 일반 내보내기
            self.message_user(
                request,
                f'{len(selected_ids)}개 항목이 선택되었습니다. 일반 내보내기를 사용하세요.',
                messages.INFO
            )
    
    async_export_selected.short_description = '선택된 항목 비동기 내보내기'


class AsyncProjectCashBookAdmin(AsyncImportExportMixin, admin.ModelAdmin):
    """
    비동기 가져오기/내보내기 기능이 추가된 ProjectCashBook Admin
    """
    resource_classes = [ProjectCashBookResource]
    list_display = (
        'id', 'project', 'deal_date', 'sort', 'project_account_d2', 'project_account_d3',
        'content', 'trader', 'bank_account', 'formatted_income', 'formatted_outlay', 'evidence')
    list_editable = ('project_account_d2', 'project_account_d3', 'evidence')
    search_fields = ('pk', 'content', 'trader', 'note')
    list_display_links = ('project', 'deal_date')
    list_filter = (
        'project', 'sort', ('deal_date', 'rangefilter.filters.DateRangeFilter'), 'project_account_d2',
        'project_account_d3', 'is_imprest', 'installment_order', 'bank_account')
    
    actions = ['async_export_selected']
    
    def formatted_income(self, obj):
        return f'{intcomma(obj.income)} 원' if obj.income else '-'
    
    def formatted_outlay(self, obj):
        return f'{intcomma(obj.outlay)} 원' if obj.outlay else '-'
    
    formatted_income.short_description = '입금액'
    formatted_outlay.short_description = '출금액'
    
    def async_export_selected(self, request, queryset):
        """선택된 항목을 비동기로 내보내기"""
        selected_ids = list(queryset.values_list('id', flat=True))
        
        if len(selected_ids) >= 1000:
            # 비동기 처리
            job = ImportJob.objects.create(
                job_type='export',
                resource_type='project_cashbook',
                status=ImportJob.PENDING,
                creator=request.user,
                total_records=len(selected_ids)
            )
            
            task = async_export_cashbook.delay(
                queryset_ids=selected_ids,
                user_id=request.user.id,
                resource_type='project_cashbook'
            )
            
            job.task_id = task.id
            job.status = ImportJob.PROCESSING
            job.started_at = timezone.now()
            job.save()
            
            self.message_user(
                request,
                f'{len(selected_ids)}개 항목의 비동기 내보내기가 시작되었습니다. (작업 ID: {job.id})',
                messages.SUCCESS
            )
            
            return HttpResponseRedirect(
                reverse('admin:cash_projectcashbook_async_status', args=[job.id])
            )
        else:
            # 일반 내보내기
            self.message_user(
                request,
                f'{len(selected_ids)}개 항목이 선택되었습니다. 일반 내보내기를 사용하세요.',
                messages.INFO
            )
    
    async_export_selected.short_description = '선택된 항목 비동기 내보내기'


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