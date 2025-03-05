from django.contrib import admin
from import_export.admin import ImportExportMixin
from .models import DocType, Category, LawsuitCase, Document, Link, File, Image


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
    list_display = ('id', 'company', 'project', 'sort', 'level', '__str__', 'plaintiff', 'defendant', 'case_start_date')
    list_display_links = ('__str__',)
    list_editable = ('project', 'sort', 'level', 'case_start_date',)
    list_filter = ('project', 'sort', 'level')
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
