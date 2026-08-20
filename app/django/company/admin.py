from django.contrib import admin
from import_export.admin import ImportExportMixin

from .models import Company, Logo, Department, JobGrade, Position, DutyTitle, Staff, StaffAssignment


class StaffAssignmentInline(admin.TabularInline):
    model = StaffAssignment
    extra = 1


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
    list_display = ('id', 'company', 'code', 'name', 'role', 'min_promotion_years', 'promotion_criteria')
    list_display_links = ('name',)
    list_filter = ('company',)


class PositionAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'name', 'desc')
    list_display_links = ('name',)
    list_filter = ('company',)


class DutyTitleAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'name', 'desc')
    list_display_links = ('name',)
    list_filter = ('company',)


class StaffAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'name', 'sort', 'grade', 'get_position', 'get_duty',
                    'get_department', 'email', 'status', 'date_join', 'date_leave')
    list_display_links = ('name', 'email')
    list_filter = ('company', 'sort', 'grade', 'status')
    inlines = (StaffAssignmentInline,)

    @admin.display(description='부서')
    def get_department(self, obj):
        return obj.department.name if obj.department else '-'

    @admin.display(description='직위')
    def get_position(self, obj):
        return obj.position.name if obj.position else '-'

    @admin.display(description='직책')
    def get_duty(self, obj):
        return obj.duty.name if obj.duty else '-'


class StaffAssignmentAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'staff', 'department', 'position', 'duty', 'is_primary', 'represent_type',
                    'assigned_tasks')
    list_display_links = ('staff',)
    list_filter = ('company', 'department', 'is_primary', 'duty', 'represent_type')
    search_fields = ('staff__name', 'department__name', 'assigned_tasks')


admin.site.register(Company, CompanyAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(JobGrade, JobGradeAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(DutyTitle, DutyTitleAdmin)
admin.site.register(Staff, StaffAdmin)
admin.site.register(StaffAssignment, StaffAssignmentAdmin)
