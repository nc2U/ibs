from django.contrib import admin
from import_export.admin import ImportExportMixin

from .models import (
    Company, Logo, Department, JobGrade, Position, DutyTitle,
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


class CompanyAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'ceo', 'tax_number', 'org_number', 'business_cond',
                    'business_even', 'es_date', 'op_date', 'is_default')
    list_display_links = ('name',)
    list_editable = ('is_default',)
    inlines = (LogoInline, DepartmentInline, JobGradeInline)


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
    list_display = ('id', 'company', 'rank_order', 'code', 'name', 'role_desc')
    list_display_links = ('name',)
    list_editable = ('rank_order',)
    list_filter = ('company',)
    search_fields = ('code', 'name', 'role_desc')


class ExecutiveAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'staff', 'rank', 'director_type', 'is_registered',
                    'is_standing', 'represent_type', 'term_start', 'term_end')
    list_display_links = ('staff',)
    list_filter = ('company', 'rank', 'director_type', 'is_registered', 'is_standing', 'represent_type')
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

