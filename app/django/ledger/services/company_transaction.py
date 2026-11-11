from collections import defaultdict
from django.db.models import Q, Subquery, IntegerField, F, OuterRef, Sum
from django.db.models.functions import Coalesce

from ledger.models import CompanyBankTransaction, CompanyAccount, CompanyAccountingEntry


def _get_descendant_account_ids(seed_ids):
    """주어진 본사 계정 ID 목록과 그 하위(자손) 활성 계정 ID들을 단일 쿼리 트리 탐색으로 반환합니다."""
    seed_set = set(seed_ids)
    if not seed_set:
        return set()

    rows = CompanyAccount.objects.filter(is_active=True).values_list('id', 'parent_id')
    active_ids = set()
    children_map = defaultdict(list)
    for acc_id, parent_id in rows:
        active_ids.add(acc_id)
        if parent_id is not None:
            children_map[parent_id].append(acc_id)

    result = set()
    queue = [acc_id for acc_id in seed_set if acc_id in active_ids]
    while queue:
        current = queue.pop()
        if current not in result:
            result.add(current)
            queue.extend(children_map.get(current, ()))
    return result


def get_company_transactions(params, base_qs=None):
    """
    본사 은행 거래 내역을 필터링하고 검색하는 공용 함수

    :param params: request.GET 또는 request.query_params (dict-like object)
    :param base_qs: RLS 등이 적용된 기본 쿼리셋 (선택)
    :return: 필터링되고 정렬된 CompanyBankTransaction 쿼리셋
    """
    qs = base_qs if base_qs is not None else CompanyBankTransaction.objects.all()

    company_id = params.get('company')
    if company_id:
        qs = qs.filter(company_id=company_id)

    # 기본 필터링
    from_deal_date = params.get('from_deal_date')
    if from_deal_date:
        qs = qs.filter(deal_date__gte=from_deal_date)

    to_deal_date = params.get('to_deal_date')
    if to_deal_date:
        qs = qs.filter(deal_date__lte=to_deal_date)

    sort = params.get('sort')
    if sort:
        qs = qs.filter(sort_id=sort)

    bank_account = params.get('bank_account')
    if bank_account:
        qs = qs.filter(bank_account_id=bank_account)

    # is_balanced 필터링 (회계분개 금액 합계와 은행 거래 금액 비교)
    is_balanced = params.get('is_balanced')
    if is_balanced is not None and is_balanced != '' and is_balanced != 'all':
        is_balanced_bool = is_balanced.lower() in ('true', '1', 'yes') if isinstance(is_balanced, str) else bool(
            is_balanced)
        entry_sum_sq = CompanyAccountingEntry.objects.filter(
            transaction_id=OuterRef('transaction_id')
        ).values('transaction_id').annotate(
            total=Sum('amount')
        ).values('total')

        qs = qs.annotate(
            calc_entry_sum=Coalesce(Subquery(entry_sum_sq, output_field=IntegerField()), 0)
        )
        if is_balanced_bool:
            qs = qs.filter(amount=F('calc_entry_sum'))
        else:
            qs = qs.exclude(amount=F('calc_entry_sum'))

    # 회계분개 모델을 참조해야 하는 복합 필터링
    account_id = params.get('account')
    account_category = params.get('account_category')
    affiliate_id = params.get('affiliate')
    search = params.get('search')

    entry_filters = Q()

    if account_id:
        try:
            account = CompanyAccount.objects.get(pk=account_id)
        except (CompanyAccount.DoesNotExist, ValueError, TypeError):
            return CompanyBankTransaction.objects.none()
        active_accounts = _get_descendant_account_ids([account.pk])
        entry_filters &= Q(account_id__in=active_accounts)

    if account_category:
        account_ids = CompanyAccount.objects.filter(
            category=account_category, is_active=True
        ).values_list('pk', flat=True)
        entry_filters &= Q(account_id__in=account_ids)

    if affiliate_id:
        entry_filters &= Q(affiliate_id=affiliate_id)

    # entry_filters가 있는 경우, transaction_id를 통해 AND 필터링
    if entry_filters:
        transaction_ids = CompanyAccountingEntry.objects.filter(
            entry_filters
        ).values_list('transaction_id', flat=True).distinct()
        qs = qs.filter(transaction_id__in=transaction_ids)

    # search가 있는 경우, 거래 필드 또는 분개(계정명+하위계정 / 거래처) 매칭으로 AND 필터링
    if search:
        search_entry_q = Q(trader__icontains=search)
        matched_seed_ids = list(CompanyAccount.objects.filter(
            name__icontains=search, is_active=True
        ).values_list('id', flat=True))

        if matched_seed_ids:
            search_account_ids = _get_descendant_account_ids(matched_seed_ids)
            if search_account_ids:
                search_entry_q |= Q(account_id__in=search_account_ids)

        search_transaction_ids = CompanyAccountingEntry.objects.filter(
            search_entry_q
        ).values_list('transaction_id', flat=True).distinct()

        qs = qs.filter(
            Q(transaction_id__icontains=search) |
            Q(content__icontains=search) |
            Q(note__icontains=search) |
            Q(transaction_id__in=search_transaction_ids)
        )

    # 정렬 및 반환
    return qs.select_related(
        'company', 'bank_account', 'sort', 'creator'
    ).order_by('-deal_date', '-created_at')


def prefetch_company_transactions(instances):
    """지정된 거래 목록(instances)에 대해서만 분개를 수동 prefetch 맵핑합니다."""
    transaction_ids = [t.transaction_id for t in instances if t.transaction_id]
    if not transaction_ids:
        for tx in instances:
            tx.prefetched_accounting_entries = []
        return instances

    # 페이징된 instances 대상 분개 쿼리 실행
    entries_qs = CompanyAccountingEntry.objects.filter(
        transaction_id__in=transaction_ids
    ).select_related(
        'company',
        'account',
        'account__parent',
        'account__parent__parent',
        'account__parent__parent__parent',
        'affiliate',
        'affiliate__company',
        'affiliate__project',
    )

    entries_map = defaultdict(list)
    for entry in entries_qs:
        entries_map[entry.transaction_id].append(entry)

    for tx in instances:
        tx_entries = entries_map.get(tx.transaction_id, [])
        for entry in tx_entries:
            entry._related_transaction = tx
        tx.prefetched_accounting_entries = tx_entries

    return instances
