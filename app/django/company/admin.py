from django.contrib import admin
from import_export.admin import ImportExportMixin

from .models import Company, Logo, Department, JobGrade, Position, DutyTitle, Staff


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
    list_display = ('id', 'company', 'upper_depart', 'name', 'level', 'task')
    list_display_links = ('name',)
    list_filter = ('company',)


class JobGradeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'name', 'promotion_period', 'criteria_new')
    list_display_links = ('name',)


class PositionAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'name', 'desc')
    list_display_links = ('name',)
    list_filter = ('company',)


class DutyTitleAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'name', 'desc')
    list_display_links = ('name',)
    list_filter = ('company',)


class StaffAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'sort', 'grade', 'position', 'duty',
                    'name', 'email', 'department', 'status', 'date_join', 'date_leave')
    list_display_links = ('name', 'email')
    list_filter = ('company', 'sort', 'grade', 'position', 'duty')


admin.site.register(Company, CompanyAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(JobGrade, JobGradeAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(DutyTitle, DutyTitleAdmin)
admin.site.register(Staff, StaffAdmin)
