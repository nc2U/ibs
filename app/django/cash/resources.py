from django.db import transaction
from import_export import resources
from import_export.instance_loaders import CachedInstanceLoader
from .models import CashBook, ProjectCashBook
import threading


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
            'project', 'content', 'trader', 'bank_account', 'income', 'outlay',
            'evidence', 'deal_date', 'note'
        )
        export_order = (
            'id', 'deal_date', 'sort', 'account_d1', 'account_d2', 'account_d3',
            'content', 'trader', 'bank_account', 'income', 'outlay', 'evidence', 'note'
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
        dry_run = kwargs.get('dry_run', False)

        # Send summary notification only after actual import (not dry_run)
        if not dry_run and len(dataset) > 0:
            self._send_bulk_import_summary(result)

        # Clear thread-local flag after both dry_run and actual import
        set_bulk_import_active(False)
        return super().after_import(dataset, result, **kwargs)

    def _send_bulk_import_summary(self, result):
        """Send Slack summary notification for bulk import"""
        from _utils.slack_notifications import send_bulk_import_summary

        summary_data = {
            'model_name': 'CashBook',
            'total_records': result.totals.get('new', 0) + result.totals.get('update', 0),
            'new_records': result.totals.get('new', 0),
            'updated_records': result.totals.get('update', 0),
            'skipped_records': result.totals.get('skip', 0),
            'error_count': result.totals.get('error', 0)
        }

        # Try to get user from request context if available
        user = None
        try:
            from django.contrib.auth import get_user
            from django.http import HttpRequest
            import threading
            request = getattr(threading.current_thread(), 'request', None)
            if request and hasattr(request, 'user'):
                user = request.user if request.user.is_authenticated else None
        except:
            pass

        send_bulk_import_summary(summary_data, user)
        
    def import_data(self, dataset, dry_run=False, raise_errors=False, use_transactions=None, collect_failed_rows=False, **kwargs):
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
                                    use_transactions=use_transactions, collect_failed_rows=collect_failed_rows, **kwargs)
    
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
            'contract', 'installment_order', 'content', 'trader', 'bank_account',
            'income', 'outlay', 'evidence', 'deal_date', 'note'
        )
        export_order = (
            'id', 'project', 'deal_date', 'sort', 'project_account_d2', 'project_account_d3',
            'content', 'trader', 'bank_account', 'income', 'outlay', 'evidence', 'note'
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
        dry_run = kwargs.get('dry_run', False)

        # Send summary notification only after actual import (not dry_run)
        if not dry_run and len(dataset) > 0:
            self._send_bulk_import_summary(result)

        # Clear thread-local flag after both dry_run and actual import
        set_bulk_import_active(False)
        return super().after_import(dataset, result, **kwargs)

    def _send_bulk_import_summary(self, result):
        """Send Slack summary notification for bulk import"""
        from _utils.slack_notifications import send_bulk_import_summary

        summary_data = {
            'model_name': 'ProjectCashBook',
            'total_records': result.totals.get('new', 0) + result.totals.get('update', 0),
            'new_records': result.totals.get('new', 0),
            'updated_records': result.totals.get('update', 0),
            'skipped_records': result.totals.get('skip', 0),
            'error_count': result.totals.get('error', 0)
        }

        # Try to get user from request context if available
        user = None
        try:
            from django.contrib.auth import get_user
            from django.http import HttpRequest
            import threading
            request = getattr(threading.current_thread(), 'request', None)
            if request and hasattr(request, 'user'):
                user = request.user if request.user.is_authenticated else None
        except:
            pass

        send_bulk_import_summary(summary_data, user)
        
    def import_data(self, dataset, dry_run=False, raise_errors=False, use_transactions=None, collect_failed_rows=False, **kwargs):
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
                                    use_transactions=use_transactions, collect_failed_rows=collect_failed_rows, **kwargs)
    
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