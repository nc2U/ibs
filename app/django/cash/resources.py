import threading

from django.db import transaction
from import_export import resources

from .models import CashBook, ProjectCashBook

# Thread-local storage for bulk import flags
_thread_locals = threading.local()


def is_bulk_import_active():
    """Check if bulk import is currently active in this thread"""
    return getattr(_thread_locals, 'bulk_import_active', False)


def set_bulk_import_active(active=True):
    """Set bulk import flag for current thread"""
    _thread_locals.bulk_import_active = active


class CashBookResource(resources.ModelResource):
    """
    Optimized resource for CashBook with bulk operations and performance improvements
    """

    class Meta:
        model = CashBook
        batch_size = 1000
        use_transactions = True
        chunk_size = 1000
        import_id_fields = ('id',)
        fields = (
            'id', 'company', 'sort', 'account_d1', 'account_d2', 'account_d3',
            'project', 'is_return', 'is_separate', 'separated', 'content', 'trader',
            'bank_account', 'income', 'outlay', 'evidence', 'deal_date', 'note'
        )
        export_order = (
            'id', 'deal_date', 'sort', 'account_d1', 'account_d2', 'account_d3',
            'project', 'is_return', 'is_separate', 'separated', 'content', 'trader',
            'bank_account', 'income', 'outlay', 'evidence', 'deal_date', 'note'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use cached instance loader for better performance
        self._cached_instances = {}
        self._bulk_import_active = False

    def before_import(self, dataset, **kwargs):
        """Set bulk import flag before starting import"""
        # Set thread-local flag for both dry_run and actual import to prevent notifications
        set_bulk_import_active(True)
        return super().before_import(dataset, **kwargs)

    def after_import(self, dataset, result, **kwargs):
        """Clear bulk import flag after import"""
        # Clear thread-local flag after both dry_run and actual import
        set_bulk_import_active(False)
        return super().after_import(dataset, result, **kwargs)

    def import_data(self, dataset, dry_run=False, raise_errors=False, use_transactions=None, collect_failed_rows=False,
                    **kwargs):
        """
        Override to use batch processing for better performance
        """
        if use_transactions is None:
            use_transactions = getattr(self.Meta, 'use_transactions', True)

        # Use batch processing for large datasets
        batch_size = getattr(self.Meta, 'batch_size', 1000)

        if not dry_run and len(dataset) > batch_size:
            return self._batch_import_data(dataset, raise_errors, use_transactions, collect_failed_rows, **kwargs)
        else:
            return super().import_data(dataset, dry_run=dry_run, raise_errors=raise_errors,
                                       use_transactions=use_transactions, collect_failed_rows=collect_failed_rows,
                                       **kwargs)

    def _batch_import_data(self, dataset, raise_errors, use_transactions, collect_failed_rows, **kwargs):
        """
        Process large datasets in batches for better performance
        """
        from import_export.results import Result

        batch_size = getattr(self.Meta, 'batch_size', 1000)
        total_result = Result()

        # Process in batches
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i:i + batch_size]

            if use_transactions:
                with transaction.atomic():
                    batch_result = super().import_data(
                        batch, dry_run=False, raise_errors=raise_errors,
                        use_transactions=False, collect_failed_rows=collect_failed_rows, **kwargs
                    )
            else:
                batch_result = super().import_data(
                    batch, dry_run=False, raise_errors=raise_errors,
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
            if batch_result.row_errors:
                total_result.row_errors.extend(batch_result.row_errors)
            if batch_result.invalid_rows:
                total_result.invalid_rows.extend(batch_result.invalid_rows)

        return total_result

    def before_import_row(self, row, **kwargs):
        """
        Pre-process row data before import
        """
        # Robust ID handling - clean up various empty/invalid ID values
        if 'id' in row:
            id_value = str(row['id']).strip() if row['id'] is not None else ''
            # Check for various empty states
            if (not id_value or
                id_value == '0' or
                id_value.lower() in ['none', 'null', 'nan'] or
                id_value == '-' or
                all(c in ' \t\n\r\xa0' for c in id_value)):  # various whitespace chars
                row['id'] = None

        # Convert empty strings to None for numeric fields
        for field in ['income', 'outlay']:
            if field in row and (row[field] == '' or row[field] is None):
                row[field] = None

        return super().before_import_row(row, **kwargs)

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """
        Skip rows with validation errors or duplicates
        """
        # Skip if both income and outlay are empty
        if not instance.income and not instance.outlay:
            return True

        # Skip if deal_date is missing
        if not instance.deal_date:
            return True

        return super().skip_row(instance, original, row, import_validation_errors)


class ProjectCashBookResource(resources.ModelResource):
    """
    Optimized resource for ProjectCashBook with bulk operations and performance improvements
    """

    class Meta:
        model = ProjectCashBook
        batch_size = 1000
        use_transactions = True
        chunk_size = 1000
        import_id_fields = ('id',)
        fields = (
            'id', 'project', 'sort', 'project_account_d2', 'project_account_d3',
            'is_separate', 'separated', 'is_imprest', 'contract', 'installment_order',
            'refund_contractor', 'content', 'trader', 'bank_account', 'income', 'outlay',
            'evidence', 'deal_date', 'note'
        )
        export_order = (
            'id', 'project', 'deal_date', 'sort', 'project_account_d2', 'project_account_d3',
            'is_separate', 'separated', 'is_imprest', 'contract', 'installment_order',
            'refund_contractor', 'content', 'trader', 'bank_account', 'income', 'outlay',
            'evidence', 'deal_date', 'note'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use cached instance loader for better performance
        self._cached_instances = {}
        self._bulk_import_active = False

    def before_import(self, dataset, **kwargs):
        """Set bulk import flag before starting import"""
        # Set thread-local flag for both dry_run and actual import to prevent notifications
        set_bulk_import_active(True)
        return super().before_import(dataset, **kwargs)

    def after_import(self, dataset, result, **kwargs):
        """Clear bulk import flag after import"""
        # Clear thread-local flag after both dry_run and actual import
        set_bulk_import_active(False)
        return super().after_import(dataset, result, **kwargs)

    def import_data(self, dataset, dry_run=False, raise_errors=False, use_transactions=None, collect_failed_rows=False,
                    **kwargs):
        """
        Override to use batch processing for better performance
        """
        if use_transactions is None:
            use_transactions = getattr(self.Meta, 'use_transactions', True)

        # Use batch processing for large datasets
        batch_size = getattr(self.Meta, 'batch_size', 1000)

        if not dry_run and len(dataset) > batch_size:
            return self._batch_import_data(dataset, raise_errors, use_transactions, collect_failed_rows, **kwargs)
        else:
            return super().import_data(dataset, dry_run=dry_run, raise_errors=raise_errors,
                                       use_transactions=use_transactions, collect_failed_rows=collect_failed_rows,
                                       **kwargs)

    def _batch_import_data(self, dataset, raise_errors, use_transactions, collect_failed_rows, **kwargs):
        """
        Process large datasets in batches for better performance
        """
        from import_export.results import Result

        batch_size = getattr(self.Meta, 'batch_size', 1000)
        total_result = Result()

        # Process in batches
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i:i + batch_size]

            if use_transactions:
                with transaction.atomic():
                    batch_result = super().import_data(
                        batch, dry_run=False, raise_errors=raise_errors,
                        use_transactions=False, collect_failed_rows=collect_failed_rows, **kwargs
                    )
            else:
                batch_result = super().import_data(
                    batch, dry_run=False, raise_errors=raise_errors,
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
            if batch_result.row_errors:
                total_result.row_errors.extend(batch_result.row_errors)
            if batch_result.invalid_rows:
                total_result.invalid_rows.extend(batch_result.invalid_rows)

        return total_result

    def before_import_row(self, row, **kwargs):
        """
        Pre-process row data before import
        """
        # Robust ID handling - clean up various empty/invalid ID values
        if 'id' in row:
            id_value = str(row['id']).strip() if row['id'] is not None else ''
            # Check for various empty states
            if (not id_value or
                id_value == '0' or
                id_value.lower() in ['none', 'null', 'nan'] or
                id_value == '-' or
                all(c in ' \t\n\r\xa0' for c in id_value)):  # various whitespace chars
                row['id'] = None

        # Convert empty strings to None for numeric fields
        for field in ['income', 'outlay']:
            if field in row and (row[field] == '' or row[field] is None):
                row[field] = None

        return super().before_import_row(row, **kwargs)

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """
        Skip rows with validation errors or duplicates
        """
        # Skip if both income and outlay are empty
        if not instance.income and not instance.outlay:
            return True

        # Skip if deal_date is missing
        if not instance.deal_date:
            return True

        # Skip if project is missing
        if not instance.project:
            return True

        return super().skip_row(instance, original, row, import_validation_errors)
