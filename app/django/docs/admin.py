from django.contrib import admin
from import_export.admin import ImportExportMixin
from .models import (
    DocType, Category, LawsuitCase, Document, Link, File, Image,
    LetterSequence, OfficialLetter
)


@admin.register(DocType)
class DocTypeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'type')
    list_display_links = ('type',)
    search_fields = ('type',)


@admin.register(Category)
class CategoryAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'doc_type', 'color', 'name', 'parent', 'order', 'active', 'default')
    list_display_links = ('name',)
    list_editable = ('doc_type', 'color', 'parent', 'order', 'active', 'default')
    search_fields = ('name',)
    list_filter = ('doc_type',)


@admin.register(LawsuitCase)
class LawsuitCaseAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'issue_project', 'sort', 'level', '__str__', 'plaintiff', 'defendant', 'case_start_date')
    list_display_links = ('__str__',)
    list_editable = ('issue_project', 'sort', 'level', 'case_start_date',)
    list_filter = ('issue_project', 'sort', 'level')
    search_fields = ('case_number', 'case_name', 'plaintiff', 'defendant')


class LinkInline(admin.TabularInline):
    model = Link
    extra = 1


class FileInline(admin.TabularInline):
    model = File
    extra = 1


class ImageInline(admin.TabularInline):
    model = Image
    extra = 1


# @admin.register(File)
# class FileAdmin(ImportExportMixin, admin.ModelAdmin):
#     list_display = ('id', 'docs', 'file_name')
#     list_filter = ('docs__company', 'docs__project')


@admin.register(Document)
class DocumentAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'doc_type', 'issue_project', 'category', 'title', 'execution_date')
    list_display_links = ('title',)
    list_editable = ('doc_type', 'issue_project', 'category', 'execution_date')
    search_fields = ('title', 'content')
    list_filter = ('doc_type', 'issue_project__company', 'issue_project__project', 'issue_project', 'category')
    inlines = (LinkInline, FileInline, ImageInline)


@admin.register(LetterSequence)
class LetterSequenceAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'company', 'year', 'last_sequence')
    list_display_links = ('company',)
    list_filter = ('company', 'year')
    search_fields = ('company__name',)


@admin.register(OfficialLetter)
class OfficialLetterAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'document_number', 'company', 'title', 'recipient_name', 'issue_date', 'creator')
    list_display_links = ('document_number', 'title')
    list_filter = ('company', 'issue_date', 'creator')
    search_fields = ('document_number', 'title', 'recipient_name', 'sender_name', 'content')
    readonly_fields = ('document_number', 'created', 'updated')
    date_hierarchy = 'issue_date'
    fieldsets = (
        ('기본 정보', {
            'fields': ('company', 'document_number', 'title', 'issue_date')
        }),
        ('수신처 정보', {
            'fields': ('recipient_name', 'recipient_address', 'recipient_contact', 'recipient_reference')
        }),
        ('발신자 정보', {
            'fields': ('sender_name', 'sender_position', 'sender_department')
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
