from django.contrib import admin
from django.db import models
from mdeditor.widgets import MDEditorWidget
from import_export.admin import ImportExportMixin
from . models import Book, Subject, Image


class BooksAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'translator', 'publisher', 'pub_date')
    search_fields = ('title', 'author', 'translator', 'publisher')
    list_display_links = ('title',)
    list_filter = ('pub_date',)
    formfield_overrides = {
        models.TextField: {'widget': MDEditorWidget}
    }

class ImagesInline(admin.StackedInline):
    model = Image
    extra = 1

class SubjectAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'book', 'seq', 'title', 'level', 'created', 'updated')
    list_display_links = ('title',)
    search_fields = ('title', 'content')
    list_filter = ('book',)
    inlines = (ImagesInline,)

admin.site.register(Book, BooksAdmin)
admin.site.register(Subject, SubjectAdmin)
