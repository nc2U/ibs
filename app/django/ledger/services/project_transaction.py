from django.db.models import Q
from collections import defaultdict

from ledger.models import ProjectBankTransaction, ProjectAccount, ProjectAccountingEntry


def get_project_transactions(params):
    """
    프로젝트 은행 거래 내역을 필터링하고 검색하는 공용 함수

    :param params: request.GET 또는 request.query_params (dict-like object)
    :return: 필터링되고 정렬된 ProjectBankTransaction 쿼리셋
    """
    qs = ProjectBankTransaction.objects.all()

    project_id = params.get('project')
    if project_id:
        qs = qs.filter(project_id=project_id)

    # 기본 필터링
    from_date = params.get('from_date')
    if from_date:
        qs = qs.filter(deal_date__gte=from_date)

    to_date = params.get('to_date')
    if to_date:
        qs = qs.filter(deal_date__lte=to_date)

    sort = params.get('sort')
    if sort:
        qs = qs.filter(sort_id=sort)

    bank_account = params.get('bank_account')
    if bank_account:
        qs = qs.filter(bank_account_id=bank_account)

    # is_imprest 필터링 (bank_account의 is_imprest 속성 사용)
    is_imprest = params.get('is_imprest')

    # is_imprest 파라미터가 없거나 빈 문자열이면 필터링하지 않음
    if is_imprest is not None and is_imprest != 'all' and is_imprest != '':
        is_imprest_bool = None
        if isinstance(is_imprest, str):
            val = is_imprest.lower()
            if val in ('true', '1', 'yes'):
                is_imprest_bool = True
            elif val in ('false', '0', 'no'):
                is_imprest_bool = False
        else:  # bool, int 등 다른 타입 처리
            is_imprest_bool = bool(is_imprest)

        # is_imprest_bool이 결정된 경우(True 또는 False)에만 필터링 적용
        if is_imprest_bool is not None:
            qs = qs.filter(bank_account__is_imprest=is_imprest_bool)

    # 회계분개 모델을 참조해야 하는 복합 필터링
    account_id = params.get('account')
    account_category = params.get('account_category')
    account_name = params.get('account_name')
    contract = params.get('contract')
    search = params.get('search')

    entry_filters = Q()

    if account_id:
        try:
            account = ProjectAccount.objects.get(pk=account_id)
        except ProjectAccount.DoesNotExist:
            return ProjectBankTransaction.objects.none()
        active_accounts = ProjectAccount.objects.filter(
            code__startswith=account.code, is_active=True
        ).values_list('pk', flat=True)
        entry_filters &= Q(account_id__in=active_accounts)

    if account_category:
        account_ids = ProjectAccount.objects.filter(
            category=account_category, is_active=True
        ).values_list('pk', flat=True)
        entry_filters &= Q(account_id__in=account_ids)

    if account_name:
        # 계정 이름으로 부분 일치 검색 — 매칭된 계정 + 하위 계정들을 code__startswith로 단일 쿼리 수집
        matched_codes = list(ProjectAccount.objects.filter(
            name__icontains=account_name, is_active=True
        ).values_list('code', flat=True))

        if matched_codes:
            account_q = Q()
            for code in matched_codes:
                account_q |= Q(code__startswith=code)
            account_ids = ProjectAccount.objects.filter(
                account_q, is_active=True
            ).values_list('pk', flat=True)
            entry_filters &= Q(account_id__in=account_ids)

    if contract:
        entry_filters &= Q(contract_id=contract)

    if search:
        search_q = Q()
        # 계정 이름 검색 — 매칭된 계정 + 하위 계정들을 code__startswith로 단일 쿼리 수집
        matched_codes = list(ProjectAccount.objects.filter(
            name__icontains=search, is_active=True
        ).values_list('code', flat=True))

        if matched_codes:
            account_q = Q()
            for code in matched_codes:
                account_q |= Q(code__startswith=code)
            account_ids = ProjectAccount.objects.filter(
                account_q, is_active=True
            ).values_list('pk', flat=True)
            search_q |= Q(account_id__in=account_ids)

        # trader 검색 추가
        search_q |= Q(trader__icontains=search)

        # 조립된 search_q 조건을 기존 필터에 AND 결합
        entry_filters &= search_q

    # entry_filters가 있는 경우, transaction_id를 통해 필터링
    if entry_filters:
        transaction_ids = ProjectAccountingEntry.objects.filter(
            entry_filters
        ).values_list('transaction_id', flat=True).distinct()

        # search가 있는 경우 OR 조건, 없는 경우 AND 조건
        if search:
            # trader 검색을 위한 추가 transaction_ids
            trader_transaction_ids = ProjectAccountingEntry.objects.filter(
                trader__icontains=search
            ).values_list('transaction_id', flat=True).distinct()

            # 기존 조건과 trader 조건을 합침
            all_transaction_ids = set(transaction_ids) | set(trader_transaction_ids)

            qs = qs.filter(
                Q(transaction_id__icontains=search) |
                Q(content__icontains=search) |
                Q(note__icontains=search) |
                Q(project__name__icontains=search) |
                Q(transaction_id__in=all_transaction_ids)
            )
        else:
            qs = qs.filter(transaction_id__in=transaction_ids)
    elif search:
        # entry_filters는 없지만 search는 있는 경우
        # trader 검색을 위한 transaction_ids
        trader_transaction_ids = ProjectAccountingEntry.objects.filter(
            trader__icontains=search
        ).values_list('transaction_id', flat=True).distinct()

        qs = qs.filter(
            Q(transaction_id__icontains=search) |
            Q(content__icontains=search) |
            Q(note__icontains=search) |
            Q(project__name__icontains=search) |
            Q(transaction_id__in=trader_transaction_ids)
        )

    # 느슨한 관계(Loose Relationship)이므로 메모리에서 수동으로 분개 데이터 Prefetch 맵핑 수행
    obj_list = list(qs.select_related(
        'project', 'bank_account', 'sort', 'creator'
    ).order_by('-deal_date', '-created_at'))

    transaction_ids = [t.transaction_id for t in obj_list]
    if transaction_ids:
        entries_qs = ProjectAccountingEntry.objects.filter(
            transaction_id__in=transaction_ids
        ).select_related('account', 'contract', 'contractor')

        if entry_filters:
            entries_qs = entries_qs.filter(entry_filters)
        elif search:
            entries_qs = entries_qs.filter(trader__icontains=search)

        entries_map = defaultdict(list)
        for entry in entries_qs:
            entries_map[entry.transaction_id].append(entry)

        for tx in obj_list:
            tx.prefetched_accounting_entries = entries_map.get(tx.transaction_id, [])
    else:
        for tx in obj_list:
            tx.prefetched_accounting_entries = []

    return obj_list
