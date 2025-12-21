from django.contrib.auth import get_user_model
from django.db import transaction
from import_export import resources, fields, widgets
from import_export.results import Result
from tablib import Dataset

from company.models import Company
from ibs.models import AccountSort
from ledger.services.sync_payment_contract import set_bulk_import_active, _sync_contract_payment_for_entry
from .models import (
    CompanyBankTransaction, ProjectBankTransaction,
    CompanyAccountingEntry, ProjectAccountingEntry, CompanyBankAccount
)

User = get_user_model()


class BaseTransactionResource(resources.ModelResource):
    """
    Base resource class for transaction models with optimized bulk operations
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cached_instances = {}

    def before_import(self, dataset, **kwargs):
        """Set bulk import flag before starting import"""
        set_bulk_import_active(True)
        return super().before_import(dataset, **kwargs)

    def after_import(self, dataset, result, **kwargs):
        """Clear bulk import flag after import"""
        set_bulk_import_active(False)
        return super().after_import(dataset, result, **kwargs)

    def import_data(self, dataset, dry_run=False, raise_errors=False, use_transactions=None, collect_failed_rows=False,
                    **kwargs):
        """
        Entry point for import.
        Ensures bulk import state is always correctly set and cleared.
        """
        if use_transactions is None:
            use_transactions = getattr(self.Meta, 'use_transactions', True)

        batch_size = getattr(self.Meta, 'batch_size', 1000)

        # dry_run에서는 bulk flag를 건드리지 않음

        if dry_run:
            return super().import_data(dataset, dry_run=dry_run, raise_errors=raise_errors,
                                       use_transactions=use_transactions,
                                       collect_failed_rows=collect_failed_rows, **kwargs)

        set_bulk_import_active(True)
        try:
            if len(dataset) > batch_size:
                return self._batch_import_data(dataset, raise_errors, use_transactions, collect_failed_rows, **kwargs)
            else:
                return super().import_data(dataset, dry_run=dry_run, raise_errors=raise_errors,
                                           use_transactions=use_transactions, collect_failed_rows=collect_failed_rows,
                                           **kwargs)
        finally:
            set_bulk_import_active(False)

    def _batch_import_data(self, dataset, raise_errors, use_transactions, collect_failed_rows, **kwargs):
        """Process large datasets in batches for better performance"""
        batch_size = getattr(self.Meta, 'batch_size', 1000)
        total_result = Result()

        for i in range(0, len(dataset), batch_size):
            # Create a new Dataset object for batch to preserve headers
            batch_data = Dataset()
            batch_data.headers = dataset.headers
            for row in dataset[i:i + batch_size]:
                batch_data.append(row)

            if use_transactions:
                with transaction.atomic():
                    batch_result = super().import_data(
                        batch_data, dry_run=False, raise_errors=raise_errors,
                        use_transactions=False, collect_failed_rows=collect_failed_rows, **kwargs
                    )
            else:
                batch_result = super().import_data(
                    batch_data, dry_run=False, raise_errors=raise_errors,
                    use_transactions=False, collect_failed_rows=collect_failed_rows, **kwargs
                )

            # Merge results
            total_result.totals['new'] += batch_result.totals.get('new', 0)
            total_result.totals['update'] += batch_result.totals.get('update', 0)
            total_result.totals['delete'] += batch_result.totals.get('delete', 0)
            total_result.totals['skip'] += batch_result.totals.get('skip', 0)
            total_result.totals['error'] += batch_result.totals.get('error', 0)

            if batch_result.base_errors:
                total_result.base_errors.extend(batch_result.base_errors)

            if batch_result.has_errors():
                total_result.error_rows.extend(batch_result.error_rows)

            if batch_result.has_validation_errors():
                total_result.invalid_rows.extend(batch_result.invalid_rows)

        return total_result

    def before_import_row(self, row, **kwargs):
        """Pre-process row data before import"""
        # Robust ID handling
        if 'id' in row:
            id_value = str(row['id']).strip() if row['id'] is not None else ''
            if (not id_value or
                    id_value == '0' or
                    id_value.lower() in ['none', 'null', 'nan'] or
                    id_value == '-' or
                    all(c in ' \t\n\r\xa0' for c in id_value)):
                row['id'] = None

        return super().before_import_row(row, **kwargs)


class CompanyBankTransactionResource(BaseTransactionResource):
    """Resource for CompanyBankTransaction with bulk operations"""

    # 외래키 필드 정의 - ID로 매핑
    company = fields.Field(
        column_name='company',
        attribute='company',
        widget=widgets.ForeignKeyWidget(model=Company, field='id')
    )
    bank_account = fields.Field(
        column_name='bank_account',
        attribute='bank_account',
        widget=widgets.ForeignKeyWidget(model=CompanyBankAccount, field='id')
    )
    sort = fields.Field(
        column_name='sort',
        attribute='sort',
        widget=widgets.ForeignKeyWidget(model=AccountSort, field='id')
    )
    creator = fields.Field(
        column_name='creator',
        attribute='creator',
        widget=widgets.ForeignKeyWidget(model=User, field='id')
    )

    class Meta:
        model = CompanyBankTransaction
        batch_size = 1000
        use_transactions = True
        chunk_size = 1000
        import_id_fields = ('id',)
        skip_unchanged = True
        report_skipped = True
        fields = (
            'id', 'transaction_id', 'company', 'bank_account', 'deal_date',
            'sort', 'amount', 'content', 'note', 'creator'
        )
        export_order = (
            'id', 'transaction_id', 'company', 'bank_account', 'deal_date',
            'sort', 'amount', 'content', 'note', 'creator'
        )

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Skip rows with validation errors"""
        # Skip if required fields are missing
        if not instance.transaction_id or not instance.deal_date:
            return True
        return super().skip_row(instance, original, row, import_validation_errors)


class ProjectBankTransactionResource(BaseTransactionResource):
    """Resource for ProjectBankTransaction with bulk operations"""

    class Meta:
        model = ProjectBankTransaction
        batch_size = 1000
        use_transactions = True
        chunk_size = 1000
        import_id_fields = ('id',)
        fields = (
            'id', 'transaction_id', 'project', 'bank_account', 'deal_date',
            'sort', 'amount', 'balance', 'content', 'note', 'is_imprest', 'creator'
        )
        export_order = (
            'id', 'transaction_id', 'project', 'bank_account', 'deal_date',
            'sort', 'amount', 'balance', 'content', 'note', 'is_imprest', 'creator'
        )

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Skip rows with validation errors"""
        # Skip if required fields are missing
        if not instance.transaction_id or not instance.deal_date:
            return True
        return super().skip_row(instance, original, row, import_validation_errors)


class CompanyAccountingEntryResource(BaseTransactionResource):
    """Resource for CompanyAccountingEntry with bulk operations"""

    class Meta:
        model = CompanyAccountingEntry
        batch_size = 1000
        use_transactions = True
        chunk_size = 1000
        import_id_fields = ('id',)
        fields = (
            'id', 'transaction_id', 'company', 'sort', 'account', 'affiliate',
            'amount', 'trader', 'evidence_type'
        )
        export_order = (
            'id', 'transaction_id', 'company', 'sort', 'account', 'affiliate',
            'amount', 'trader', 'evidence_type'
        )

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Skip rows with validation errors"""
        # Skip if required fields are missing
        if not instance.transaction_id or not instance.account:
            return True
        return super().skip_row(instance, original, row, import_validation_errors)


class ProjectAccountingEntryResource(BaseTransactionResource):
    """Resource for ProjectAccountingEntry with bulk operations"""

    def after_save_instance(self, instance, using_transactions, dry_run):
        """
        Call the synchronization logic after each instance is saved during import.
        """
        if not dry_run:
            _sync_contract_payment_for_entry(instance)

    class Meta:
        model = ProjectAccountingEntry
        batch_size = 1000
        use_transactions = True
        chunk_size = 1000
        import_id_fields = ('id',)
        fields = (
            'id', 'transaction_id', 'project', 'sort', 'account', 'contract',
            'amount', 'trader', 'evidence_type', 'installment_order'
        )
        export_order = (
            'id', 'transaction_id', 'project', 'sort', 'account', 'contract',
            'amount', 'trader', 'evidence_type', 'installment_order'
        )

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Skip rows with validation errors"""
        # Skip if required fields are missing
        if not instance.transaction_id or not instance.account:
            return True
        return super().skip_row(instance, original, row, import_validation_errors)
