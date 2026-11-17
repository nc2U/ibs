from django.contrib import admin
from import_export.admin import ImportExportMixin

from apiV1.permissions._utils import get_company_ids_with_permission
from work.models.project import IssueProject
from .models import (
    Category, LawsuitCase, Document, Link, File, Image,
    LetterSequence, OfficialLetter, OfficialLetterAttachment,
    InboundSequence, InboundLetter, InboundLetterAttachment
)


def _is_admin_user(user):
    return bool(user and (user.is_superuser or getattr(user, 'work_manager', False)))


@admin.register(Category)
class CategoryAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'doc_type', 'color', 'name', 'parent', 'order', 'active', 'default')
    list_display_links = ('name',)
    list_select_related = ('parent',)
    list_editable = ('doc_type', 'color', 'parent', 'order', 'active', 'default')
    search_fields = ('name',)
    list_filter = ('doc_type',)


class LinkInline(admin.TabularInline):
    model = Link
    extra = 1


class FileInline(admin.TabularInline):
    model = File
    extra = 1


class ImageInline(admin.TabularInline):
    model = Image
    extra = 1


@admin.register(Document)
class DocumentAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'doc_type', 'issue_project', 'category', 'title', 'execution_date')
    list_display_links = ('title',)
    list_select_related = ('issue_project', 'category')
    list_editable = ('doc_type', 'issue_project', 'category', 'execution_date')
    search_fields = ('title', 'description')
    list_filter = ('doc_type', 'issue_project__company', 'issue_project__project', 'issue_project', 'category')
    inlines = (LinkInline, FileInline, ImageInline)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('issue_project', 'category')
        if _is_admin_user(request.user):
            return qs
        accessible_projects = IssueProject.objects.filter(members__user=request.user)
        return qs.filter(issue_project__in=accessible_projects)


@admin.register(LawsuitCase)
class LawsuitCaseAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'issue_project', 'sort', 'level', '__str__', 'plaintiff', 'defendant', 'case_start_date')
    list_display_links = ('__str__',)
    list_select_related = ('issue_project', 'related_case', 'creator')
    list_editable = ('issue_project', 'sort', 'level', 'case_start_date',)
    list_filter = ('issue_project', 'sort', 'level')
    search_fields = ('case_number', 'case_name', 'plaintiff', 'defendant')

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('issue_project', 'related_case', 'creator')
        if _is_admin_user(request.user):
            return qs
        accessible_projects = IssueProject.objects.filter(members__user=request.user)
        return qs.filter(issue_project__in=accessible_projects)


@admin.register(LetterSequence)
class LetterSequenceAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'year', 'last_sequence')
    list_display_links = ('company',)
    list_select_related = ('company',)
    list_filter = ('company', 'year')
    search_fields = ('company__name',)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('company')
        if _is_admin_user(request.user):
            return qs
        company_ids = get_company_ids_with_permission(request.user, 'docs.read')
        return qs.filter(company_id__in=company_ids)


class OfficialLetterAttachmentInline(admin.TabularInline):
    model = OfficialLetterAttachment
    extra = 1


@admin.register(OfficialLetter)
class OfficialLetterAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'document_number', 'company', 'title', 'recipient_name', 'issue_date', 'creator')
    list_display_links = ('document_number', 'title')
    list_select_related = ('company', 'creator')
    list_filter = ('company', 'issue_date', 'creator')
    search_fields = ('document_number', 'title', 'recipient_name', 'drafter_name', 'content')
    readonly_fields = ('document_number', 'created', 'updated')
    date_hierarchy = 'issue_date'
    inlines = (OfficialLetterAttachmentInline,)
    fieldsets = (
        ('기본 정보', {
            'fields': ('company', 'document_number', 'title', 'issue_date')
        }),
        ('수신처 정보', {
            'fields': ('recipient_name', 'recipient_address', 'recipient_contact', 'recipient_reference')
        }),
        ('기안/담당자 정보', {
            'fields': ('drafter_name', 'drafter_position')
        }),
        ('내용', {
            'fields': ('content',)
        }),
        ('PDF', {
            'fields': ('pdf_file',)
        }),
        ('메타데이터', {
            'fields': ('creator', 'updator', 'created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('company', 'creator')
        if _is_admin_user(request.user):
            return qs
        company_ids = get_company_ids_with_permission(request.user, 'docs.read')
        return qs.filter(company_id__in=company_ids)


@admin.register(InboundSequence)
class InboundSequenceAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'year', 'last_sequence')
    list_display_links = ('company',)
    list_select_related = ('company',)
    list_filter = ('company', 'year')
    search_fields = ('company__name',)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('company')
        if _is_admin_user(request.user):
            return qs
        company_ids = get_company_ids_with_permission(request.user, 'docs.read')
        return qs.filter(company_id__in=company_ids)


class InboundLetterAttachmentInline(admin.TabularInline):
    model = InboundLetterAttachment
    extra = 1


@admin.register(InboundLetter)
class InboundLetterAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'receipt_number', 'document_number', 'company', 'sender_name', 'title', 'received_date', 'reply_due_date', 'status')
    list_display_links = ('receipt_number', 'title')
    list_select_related = ('company', 'recipient_dept', 'recipient_manager')
    list_filter = ('company', 'status', 'received_date', 'recipient_dept')
    search_fields = ('receipt_number', 'document_number', 'sender_name', 'title', 'content')
    readonly_fields = ('receipt_number', 'created', 'updated')
    date_hierarchy = 'received_date'
    inlines = (InboundLetterAttachmentInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('company', 'recipient_dept', 'recipient_manager')
        if _is_admin_user(request.user):
            return qs
        company_ids = get_company_ids_with_permission(request.user, 'docs.read')
        return qs.filter(company_id__in=company_ids)
