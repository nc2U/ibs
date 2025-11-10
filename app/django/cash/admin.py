from datetime import timedelta

from django.contrib import admin
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils import timezone
from import_export.admin import ImportExportMixin
from rangefilter.filters import DateRangeFilter

from _utils.slack_notifications import send_bulk_import_summary
from .models import CompanyBankAccount, ProjectBankAccount, CashBook, ProjectCashBook
from .resources import CashBookResource, ProjectCashBookResource


class CompanyBankAccountAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'order', 'depart', 'bankcode', 'alias_name',
                    'number', 'holder', 'open_date', 'note', 'inactive')
    list_editable = ('order', 'number', 'inactive')
    list_display_links = ('depart', 'bankcode')
    list_filter = ('company', 'depart', 'bankcode', 'holder')


class ProjectBankAccountAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'order', 'project', 'alias_name', 'bankcode', 'number',
                    'holder', 'open_date', 'note', 'inactive', 'directpay')
    list_editable = ('order', 'number', 'inactive', 'directpay')
    list_display_links = ('project', 'bankcode')
    list_filter = ('bankcode', 'holder')


class CashBookAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_classes = [CashBookResource]
    list_display = ('id', 'deal_date', 'sort', 'account_d1', 'account_d2', 'account_d3', 'content',
                    'trader', 'bank_account', 'formatted_income', 'formatted_outlay', 'evidence', 'creator')
    list_editable = ('account_d1', 'account_d2', 'account_d3', 'content', 'trader', 'evidence')
    search_fields = ('account_d3', 'content', 'trader', 'note')
    list_display_links = ('deal_date', 'sort', 'bank_account')
    list_filter = ('company', ('deal_date', DateRangeFilter), 'sort',
                   'account_d1', 'account_d2', 'account_d3', 'evidence')

    def process_dataset(self, dataset, form, request, **kwargs):
        """Override process_dataset which is called by both dry run and actual import"""
        # Call parent process_dataset
        result = super().process_dataset(dataset, form, request, **kwargs)

        # Check if this is the final import (not dry run)
        if hasattr(form, 'cleaned_data') and not result.has_errors() and not result.has_validation_errors():
            # Check if this is the actual import (has import_file_name from confirmation form)
            is_actual_import = 'import_file_name' in form.cleaned_data

            if is_actual_import:
                try:
                    self._send_admin_import_summary_from_result(request, result)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"CashBook 요약 알림 전송 실패: {e}")
                    import traceback
                    traceback.print_exc()

        return result

    @staticmethod
    def _send_admin_import_summary_from_result(request, result):
        """Send Slack summary notification using import result data directly"""
        import logging
        logger = logging.getLogger(__name__)

        # result.totals에서 직접 데이터 가져오기
        new_records = result.totals.get('new', 0)
        updated_records = result.totals.get('update', 0)
        skipped_records = result.totals.get('skip', 0)
        error_count = result.totals.get('error', 0) + result.totals.get('invalid', 0)
        total_records = new_records + updated_records

        if total_records > 0:
            summary_data = {
                'model_name': 'CashBook',
                'total_records': total_records,
                'new_records': new_records,
                'updated_records': updated_records,
                'skipped_records': skipped_records,
                'error_count': error_count
            }

            logger.info(f"[ADMIN_IMPORT] CashBook import 결과 기반 요약: {summary_data}")

            user = request.user if request.user.is_authenticated else None

            try:
                send_bulk_import_summary(summary_data, user)
                logger.info(f"[ADMIN_IMPORT] CashBook 요약 알림 전송 완료")
            except Exception as e:
                logger.error(f"[ADMIN_IMPORT] CashBook Slack 요약 알림 전송 예외: {e}")
                import traceback
                traceback.print_exc()
        else:
            logger.info(f"[ADMIN_IMPORT] CashBook 처리된 레코드 없음")

    def formatted_income(self, obj):
        return f'{intcomma(obj.income)} 원' if obj.income else '-'

    def formatted_outlay(self, obj):
        return f'{intcomma(obj.outlay)} 원' if obj.outlay else '-'

    formatted_income.short_description = '입금액'
    formatted_outlay.short_description = '출금액'


class ProjectCashBookAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_classes = [ProjectCashBookResource]
    list_display = (
        'id', 'project', 'deal_date', 'sort', 'project_account_d2', 'project_account_d3',
        'content', 'trader', 'bank_account', 'formatted_income', 'formatted_outlay', 'evidence')
    list_editable = ('project_account_d2', 'project_account_d3', 'evidence')
    search_fields = ('pk', 'content', 'trader', 'note')
    list_display_links = ('project', 'deal_date')
    list_filter = (
        'project', 'sort', ('deal_date', DateRangeFilter), 'project_account_d2',
        'project_account_d3', 'is_imprest', 'installment_order', 'bank_account')

    def process_dataset(self, dataset, form, request, **kwargs):
        """Override process_dataset which is called by both dry run and actual import"""
        # Call parent process_dataset
        result = super().process_dataset(dataset, form, request, **kwargs)

        # Check if this is the final import (not dry run)
        if hasattr(form, 'cleaned_data') and not result.has_errors() and not result.has_validation_errors():
            # Check if this is the actual import (has import_file_name from confirmation form)
            is_actual_import = 'import_file_name' in form.cleaned_data

            if is_actual_import:
                try:
                    self._send_admin_import_summary_from_result(request, result)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"ProjectCashBook 요약 알림 전송 실패: {e}")
                    import traceback
                    traceback.print_exc()

        return result

    @staticmethod
    def _send_admin_import_summary_from_result(request, result):
        """Send Slack summary notification using import result data directly"""
        import logging
        logger = logging.getLogger(__name__)

        # result.totals에서 직접 데이터 가져오기
        new_records = result.totals.get('new', 0)
        updated_records = result.totals.get('update', 0)
        skipped_records = result.totals.get('skip', 0)
        error_count = result.totals.get('error', 0) + result.totals.get('invalid', 0)
        total_records = new_records + updated_records

        if total_records > 0:
            summary_data = {
                'model_name': 'ProjectCashBook',
                'total_records': total_records,
                'new_records': new_records,
                'updated_records': updated_records,
                'skipped_records': skipped_records,
                'error_count': error_count
            }

            logger.info(f"[ADMIN_IMPORT] ProjectCashBook import 결과 기반 요약: {summary_data}")

            user = request.user if request.user.is_authenticated else None

            # ProjectCashBook은 프로젝트별 모델이므로 최근 레코드를 target_instance로 전달
            recent_time = timezone.now() - timedelta(minutes=5)

            recent_records = ProjectCashBook.objects.filter(
                updated__gte=recent_time
            ).order_by('-updated')

            target_instance = recent_records.first() if recent_records.exists() else None

            try:
                send_bulk_import_summary(summary_data, user, target_instance)
                logger.info(f"[ADMIN_IMPORT] ProjectCashBook 요약 알림 전송 완료")
            except Exception as e:
                logger.error(f"[ADMIN_IMPORT] ProjectCashBook Slack 요약 알림 전송 예외: {e}")
                import traceback
                traceback.print_exc()
        else:
            logger.info(f"[ADMIN_IMPORT] ProjectCashBook 처리된 레코드 없음")

    def formatted_income(self, obj):
        return f'{intcomma(obj.income)} 원' if obj.income else '-'

    def formatted_outlay(self, obj):
        return f'{intcomma(obj.outlay)} 원' if obj.outlay else '-'

    formatted_income.short_description = '입금액'
    formatted_outlay.short_description = '출금액'


admin.site.register(CompanyBankAccount, CompanyBankAccountAdmin)
admin.site.register(ProjectBankAccount, ProjectBankAccountAdmin)
admin.site.register(CashBook, CashBookAdmin)
admin.site.register(ProjectCashBook, ProjectCashBookAdmin)
