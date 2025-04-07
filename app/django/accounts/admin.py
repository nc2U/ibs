from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportMixin

from .forms import UserCreationForm, UserChangeForm
from .models import User, DocScrape, StaffAuth  # , PostScrape


class StaffAuthInline(admin.StackedInline):
    model = StaffAuth


# class ProfileInline(admin.StackedInline):
#     model = Profile


# class TodosInline(admin.StackedInline):
#     model = Todo


@admin.register(User)
class UserAdmin(ImportExportMixin, BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('username', 'email', 'is_active', 'is_superuser',
                    'is_staff', 'work_manager', 'last_login', 'date_joined')
    list_filter = ('is_superuser', 'is_active',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('username',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_superuser', 'is_staff', 'work_manager')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2')}
         ),
    )
    search_fields = ('email', 'username')
    ordering = ('-date_joined',)
    filter_horizontal = ()
    inlines = (StaffAuthInline,)  # ProfileInline, TodosInline)


@admin.register(DocScrape)
class DocScrapeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'user', 'docs', 'title', 'created')
    list_display_links = ('user', 'docs')

# @admin.register(PostScrape)
# class DocScrapeAdmin(ImportExportMixin, admin.ModelAdmin):
#     list_display = ('pk', 'user', 'post', 'title', 'created')
#     list_display_links = ('user', 'post')
