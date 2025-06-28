from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.mail import send_mail
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
    actions = ['send_test_email']
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

    def send_test_email(self, request, queryset):
        # 예시: 선택된 첫 번째 객체를 기준으로 메일 전송
        obj = queryset.first()
        try:
            send_mail(
                subject='테스트 메일',
                message='이것은 Django admin 에서 발송한 테스트 메일입니다.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[obj.email],
            )
            self.message_user(request, "테스트 메일이 성공적으로 발송되었습니다.", level=messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"메일 발송 실패: {e}", level=messages.ERROR)

    send_test_email.short_description = "선택 항목에 대해 이메일 테스트 발송"


@admin.register(DocScrape)
class DocScrapeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('pk', 'user', 'docs', 'title', 'created')
    list_display_links = ('user', 'docs')

# @admin.register(PostScrape)
# class DocScrapeAdmin(ImportExportMixin, admin.ModelAdmin):
#     list_display = ('pk', 'user', 'post', 'title', 'created')
#     list_display_links = ('user', 'post')
