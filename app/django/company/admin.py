from django.contrib import admin
from import_export.admin import ImportExportMixin

from .models import (
    Company, Logo, CompanySeal, Department, JobGrade, Position, DutyTitle,
    ExecutiveRank, Executive, Staff, StaffAssignment,
    PersonnelOrder, StaffCareer, StaffCertificate, StaffRewardPunishment,
    StaffLeaveQuota, StaffLeaveUsage,
    PromotionPolicy, StaffEvaluation, PromotionCandidate
)


class StaffAssignmentInline(admin.TabularInline):
    model = StaffAssignment
    extra = 1


class PersonnelOrderInline(admin.TabularInline):
    model = PersonnelOrder
    fk_name = 'staff'
    extra = 0
    fields = ('order_date', 'order_type', 'new_department', 'new_grade', 'new_position', 'new_duty', 'description')


class StaffCareerInline(admin.TabularInline):
    model = StaffCareer
    extra = 0


class StaffCertificateInline(admin.TabularInline):
    model = StaffCertificate
    extra = 0


class StaffRewardPunishmentInline(admin.TabularInline):
    model = StaffRewardPunishment
    extra = 0


class ExecutiveInline(admin.StackedInline):
    model = Executive
    extra = 0


class DepartmentInline(admin.StackedInline):
    model = Department


class JobGradeInline(admin.StackedInline):
    model = JobGrade


class LogoInline(admin.StackedInline):
    model = Logo


class CompanySealInline(admin.TabularInline):
    model = CompanySeal
    extra = 1
    fields = ('seal_type', 'name', 'seal_image', 'manager', 'final_approval_duty', 'final_dept_level', 'is_active')


class CompanyAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'short_name', 'ceo', 'tax_number', 'org_number', 'business_cond',
                    'business_even', 'es_date', 'op_date', 'is_default')
    list_display_links = ('name',)
    list_editable = ('is_default',)
    inlines = (LogoInline, CompanySealInline, DepartmentInline, JobGradeInline)


@admin.register(CompanySeal)
class CompanySealAdmin(ImportExportMixin, admin.ModelAdmin):
    change_list_template = 'admin/company/companyseal/change_list.html'
    list_display = (
        'id', 'company', 'seal_type', 'name', 'purpose', 'custody_type',
        'custodian', 'internal_manager', 'final_approval_duty', 'final_dept_level',
        'route_template', 'valid_until', 'is_active', 'created'
    )
    list_display_links = ('name',)
    list_editable = ('is_active',)
    list_filter = ('company', 'seal_type', 'custody_type', 'final_approval_duty', 'is_active')
    search_fields = ('name', 'purpose', 'custodian', 'internal_manager__name')
    raw_id_fields = ('internal_manager', 'route_template')

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('extract-scan/', self.admin_site.admin_view(self.extract_scan_view), name='company_companyseal_extract_scan'),
            path('extract-scan/status/<str:task_id>/', self.admin_site.admin_view(self.extract_scan_status_view), name='company_companyseal_extract_scan_status'),
        ]
        return custom_urls + urls

    def extract_scan_status_view(self, request, task_id):
        """Celery 비동기 작업 상태를 JSON으로 반환"""
        from django.http import JsonResponse
        from django.core.cache import cache
        from celery.result import AsyncResult

        cache_key = f"seal_extraction_{task_id}"
        cached_result = cache.get(cache_key)

        if cached_result:
            return JsonResponse(cached_result)

        async_res = AsyncResult(task_id)
        if async_res.ready():
            if async_res.successful():
                return JsonResponse({'status': 'SUCCESS', 'result': async_res.result})
            else:
                return JsonResponse({'status': 'FAILURE', 'error': str(async_res.result)})

        return JsonResponse({'status': 'PROGRESS', 'message': '인장 감지 및 이미지 분석 중...'})

    def extract_scan_view(self, request):
        import os
        import tempfile
        import base64
        from django.shortcuts import render, redirect
        from django.contrib import messages
        from django.core.files.base import ContentFile
        from .seal_extractor import extract_seals_from_file

        companies = Company.objects.all().order_by('-is_default', 'id')
        duties = DutyTitle.objects.all().order_by('id')
        seal_types = CompanySeal.SEAL_TYPE_CHOICES

        if request.method == 'POST':
            step = request.POST.get('step')

            # 1단계: 스캔 파일 업로드 및 인장 자동 감지
            if step == 'upload':
                company_id = request.POST.get('company_id')
                scan_file = request.FILES.get('scan_file')

                if not company_id or not scan_file:
                    messages.error(request, '회사와 스캔 파일(PDF 또는 이미지)을 모두 선택해주세요.')
                    return redirect('admin:company_companyseal_extract_scan')

                try:
                    target_company = Company.objects.get(pk=company_id)
                except Company.DoesNotExist:
                    messages.error(request, '선택한 회사가 존재하지 않습니다.')
                    return redirect('admin:company_companyseal_extract_scan')

                is_pdf = scan_file.name.lower().endswith('.pdf')
                ext = '.pdf' if is_pdf else '.png'

                # Celery 비동기 태스크 시도 (미구동 또는 실패 시 동기 폴백)
                use_celery = True
                task_id = None

                # 파일을 공유 디렉토리(django 루트의 tmp 폴더)에 임시 저장
                tmp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tmp')
                os.makedirs(tmp_dir, exist_ok=True)
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=tmp_dir)
                try:
                    for chunk in scan_file.chunks():
                        tmp_file.write(chunk)
                    tmp_file.close()

                    if use_celery:
                        try:
                            from .tasks import extract_seals_task
                            celery_task = extract_seals_task.delay(tmp_file.name, is_pdf=is_pdf)
                            task_id = celery_task.id
                            return render(request, 'admin/company/companyseal/extract_scan.html', {
                                'title': '인장 추출 작업 진행 중',
                                'target_company': target_company,
                                'task_id': task_id,
                                'seal_types': seal_types,
                                'duties': duties,
                            })
                        except Exception as celery_err:
                            # Celery 브로커 연결 실패 시 동기로 처리
                            pass

                    # 동기 처리 (Fallback)
                    with open(tmp_file.name, 'rb') as f:
                        file_bytes = f.read()
                    detected_seals = extract_seals_from_file(file_bytes, is_pdf=is_pdf)
                    messages.success(request, f'스캔 문서에서 {len(detected_seals)}개의 인장을 감지하여 투명화 처리를 완료했습니다.')
                    return render(request, 'admin/company/companyseal/extract_scan.html', {
                        'title': '스캔 인장 확인 및 등록',
                        'target_company': target_company,
                        'detected_seals': detected_seals,
                        'seal_types': seal_types,
                        'duties': duties,
                    })
                except Exception as e:
                    messages.error(request, f'인장 추출 실패: {str(e)}')
                    return redirect('admin:company_companyseal_extract_scan')
                finally:
                    if not task_id and os.path.exists(tmp_file.name):
                        try:
                            os.remove(tmp_file.name)
                        except OSError:
                            pass

            # 2단계: 감지된 인장 정보 일괄 등록
            elif step == 'save':
                company_id = request.POST.get('company_id')
                seal_count = int(request.POST.get('seal_count', 0))

                try:
                    target_company = Company.objects.get(pk=company_id)
                except Company.DoesNotExist:
                    messages.error(request, '선택한 회사가 존재하지 않습니다.')
                    return redirect('admin:company_companyseal_changelist')

                saved_count = 0
                for i in range(seal_count):
                    name = request.POST.get(f'name_{i}', '').strip()
                    seal_type = request.POST.get(f'seal_type_{i}', 'USAGE_SEAL')
                    manager = request.POST.get(f'manager_{i}', '').strip()
                    final_duty_id = request.POST.get(f'final_duty_{i}')
                    b64_data = request.POST.get(f'seal_b64_{i}', '')

                    if not name or not b64_data:
                        continue

                    # Base64 헤더 제거 후 디코딩
                    if ',' in b64_data:
                        b64_data = b64_data.split(',', 1)[1]
                    png_bytes = base64.b64decode(b64_data)

                    duty_obj = DutyTitle.objects.filter(pk=final_duty_id).first() if final_duty_id else None

                    # CompanySeal 생성 및 저장
                    seal = CompanySeal(
                        company=target_company,
                        seal_type=seal_type,
                        name=name,
                        custodian=manager,
                        final_approval_duty=duty_obj,
                        is_active=True,
                    )
                    file_name = f"seal_{target_company.id}_{seal_type}_{i+1}.png"
                    seal.seal_image.save(file_name, ContentFile(png_bytes), save=True)
                    saved_count += 1

                messages.success(request, f'{target_company.name}에 총 {saved_count}개의 인장이 성공적으로 등록되었습니다.')
                return redirect('admin:company_companyseal_changelist')

        return render(request, 'admin/company/companyseal/extract_scan.html', {
            'title': '스캔 문서에서 인장 자동 추출',
            'companies': companies,
            'duties': duties,
            'seal_types': seal_types,
            'detected_seals': None,
        })


class DepartmentAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'upper_depart', 'name', 'level', 'task', 'manager')
    list_display_links = ('company', 'name')
    list_editable = ('task', 'manager')
    list_filter = ('company',)


class JobGradeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'code', 'role', 'min_promotion_years', 'promotion_criteria')
    list_display_links = ('code',)
    list_filter = ('company',)


class PositionAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'name', 'desc')
    list_display_links = ('name',)
    list_filter = ('company',)


class DutyTitleAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'code', 'name', 'desc')
    list_display_links = ('code', 'name')
    list_filter = ('company',)
    search_fields = ('code', 'name', 'desc')


class ExecutiveRankAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'sort_order', 'code', 'name', 'role_desc')
    list_display_links = ('name',)
    list_editable = ('sort_order',)
    list_filter = ('company',)
    search_fields = ('code', 'name', 'role_desc')


class ExecutiveAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'staff', 'rank', 'executive_type', 'is_registered',
                    'is_standing', 'represent_type', 'term_start', 'term_end')
    list_display_links = ('staff',)
    list_filter = ('company', 'rank', 'executive_type', 'is_registered', 'is_standing', 'represent_type')
    search_fields = ('staff__name', 'rank__name', 'note')


class StaffAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'name', 'sort', 'get_executive_rank', 'employment_type',
                    'grade', 'position', 'get_department', 'get_duty', 'email', 'status',
                    'date_join', 'contract_end_date', 'date_leave')
    list_display_links = ('name', 'email')
    list_filter = ('company', 'sort', 'employment_type', 'grade', 'position', 'status')
    inlines = (StaffAssignmentInline, ExecutiveInline, PersonnelOrderInline,
               StaffCareerInline, StaffCertificateInline, StaffRewardPunishmentInline)

    @admin.display(description='임원 직위')
    def get_executive_rank(self, obj):
        return obj.executive_rank or '-'

    @admin.display(description='부서')
    def get_department(self, obj):
        return obj.department.name if obj.department else '-'

    @admin.display(description='직책')
    def get_duty(self, obj):
        return obj.duty.name if obj.duty else '-'


class StaffAssignmentAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'staff', 'department', 'duty', 'is_primary',
                    'assigned_tasks')
    list_display_links = ('staff',)
    list_filter = ('company', 'department', 'is_primary', 'duty')
    search_fields = ('staff__name', 'department__name', 'assigned_tasks')


class PersonnelOrderAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'order_date', 'order_no', 'staff', 'order_type',
                    'new_department', 'new_grade', 'new_position', 'new_duty', 'is_processed')
    list_display_links = ('order_date', 'staff')
    list_filter = ('company', 'order_type', 'is_processed', 'new_department')
    search_fields = ('staff__name', 'order_no', 'description')


class StaffCareerAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'staff', 'company_name', 'department_name', 'position_title',
                    'start_date', 'end_date', 'recognized_ratio')
    list_display_links = ('company_name', 'staff')
    list_filter = ('company',)
    search_fields = ('staff__name', 'company_name', 'assigned_tasks')


class StaffCertificateAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'staff', 'name', 'grade', 'cert_number', 'issuer',
                    'acquired_date', 'expire_date', 'has_allowance')
    list_display_links = ('name', 'staff')
    list_filter = ('company', 'has_allowance')
    search_fields = ('staff__name', 'name', 'grade', 'cert_number', 'issuer')


class StaffRewardPunishmentAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'staff', 'sort', 'type_name', 'action_date', 'expire_date', 'organization')
    list_display_links = ('type_name', 'staff')
    list_filter = ('company', 'sort')
    search_fields = ('staff__name', 'type_name', 'reason', 'organization')


class PromotionPolicyAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'current_grade', 'target_grade', 'min_years',
                    'required_eval_grade', 'min_avg_grade_point', 'is_active')
    list_display_links = ('current_grade', 'target_grade')
    list_editable = ('min_years', 'is_active')
    list_filter = ('company', 'is_active')
    search_fields = ('current_grade__code', 'target_grade__code', 'required_credentials', 'disqualification_conditions')


class StaffEvaluationAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'staff', 'eval_year', 'eval_period', 'grade', 'score', 'evaluator', 'reviewer')
    list_display_links = ('staff',)
    list_filter = ('company', 'eval_year', 'eval_period', 'grade')
    search_fields = ('staff__name', 'achievement_summary', 'notes')


class PromotionCandidateAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'eval_year', 'staff', 'policy', 'tenure_years', 'avg_eval_score', 'status',
                    'promoted_date')
    list_display_links = ('staff',)
    list_editable = ('status', 'promoted_date')
    list_filter = ('company', 'eval_year', 'status', 'policy')
    search_fields = ('staff__name', 'committee_review')


class StaffLeaveQuotaAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'year', 'staff', 'granted_days', 'carry_over_days', 'reward_days',
                    'get_total_granted', 'get_used_days', 'get_remaining_days', 'valid_start', 'valid_end')
    list_display_links = ('year', 'staff')
    list_filter = ('company', 'year')
    search_fields = ('staff__name', 'note')

    @admin.display(description='총 부여(일)')
    def get_total_granted(self, obj):
        return obj.total_granted_days

    @admin.display(description='사용(일)')
    def get_used_days(self, obj):
        return obj.used_days

    @admin.display(description='잔여(일)')
    def get_remaining_days(self, obj):
        return obj.remaining_days


class StaffLeaveUsageAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'staff', 'leave_type', 'start_date', 'end_date',
                    'deduction_days', 'approval_doc', 'is_cancelled', 'created')
    list_display_links = ('staff', 'leave_type')
    list_filter = ('company', 'leave_type', 'is_cancelled', 'start_date')
    search_fields = ('staff__name', 'reason', 'approval_doc__title', 'approval_doc__doc_number')


admin.site.register(Company, CompanyAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(JobGrade, JobGradeAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(DutyTitle, DutyTitleAdmin)
admin.site.register(ExecutiveRank, ExecutiveRankAdmin)
admin.site.register(Executive, ExecutiveAdmin)
admin.site.register(Staff, StaffAdmin)
admin.site.register(StaffAssignment, StaffAssignmentAdmin)
admin.site.register(PersonnelOrder, PersonnelOrderAdmin)
admin.site.register(StaffCareer, StaffCareerAdmin)
admin.site.register(StaffCertificate, StaffCertificateAdmin)
admin.site.register(StaffRewardPunishment, StaffRewardPunishmentAdmin)
admin.site.register(StaffLeaveQuota, StaffLeaveQuotaAdmin)
admin.site.register(StaffLeaveUsage, StaffLeaveUsageAdmin)
admin.site.register(PromotionPolicy, PromotionPolicyAdmin)
admin.site.register(StaffEvaluation, StaffEvaluationAdmin)
admin.site.register(PromotionCandidate, PromotionCandidateAdmin)
