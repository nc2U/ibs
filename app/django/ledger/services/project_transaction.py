from django.db.models import Q
from collections import defaultdict

from ledger.models import ProjectBankTransaction, ProjectAccount, ProjectAccountingEntry


def _get_descendant_account_ids(seed_ids):
    """주어진 프로젝트 계정 ID 목록과 그 하위(자손) 활성 계정 ID들을 단일 쿼리 트리 탐색으로 반환합니다."""
    seed_set = set(seed_ids)
    if not seed_set:
        return set()

    rows = ProjectAccount.objects.filter(is_active=True).values_list('id', 'parent_id')
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


def get_project_transactions(params, user=None):
    """
    프로젝트 은행 거래 내역을 필터링하고 검색하는 공용 함수

    :param params: request.GET 또는 request.query_params (dict-like object)
    :param user: 요청 유저 (접근 권한 필터링용)
    :return: 필터링되고 정렬된 ProjectBankTransaction 쿼리셋
    """
    qs = ProjectBankTransaction.objects.all()

    if user and not (user.is_superuser or getattr(user, 'work_manager', False)):
        from apiV1.permissions._utils import get_project_ids_with_permission
        accessible_project_ids = get_project_ids_with_permission(user, 'ledger.read')
        qs = qs.filter(project_id__in=accessible_project_ids)

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
        except (ProjectAccount.DoesNotExist, ValueError, TypeError):
            return ProjectBankTransaction.objects.none()
        active_accounts = _get_descendant_account_ids([account.pk])
        entry_filters &= Q(account_id__in=active_accounts)

    if account_category:
        account_ids = ProjectAccount.objects.filter(
            category=account_category, is_active=True
        ).values_list('pk', flat=True)
        entry_filters &= Q(account_id__in=account_ids)

    if account_name:
        # 계정 이름으로 부분 일치 검색 — 매칭된 계정 + 하위 계정들을 parent_id 트리 탐색으로 수집
        matched_seed_ids = list(ProjectAccount.objects.filter(
            name__icontains=account_name, is_active=True
        ).values_list('id', flat=True))
        account_ids = _get_descendant_account_ids(matched_seed_ids)
        entry_filters &= Q(account_id__in=account_ids)

    if contract:
        entry_filters &= Q(contract_id=contract)

    # entry_filters가 있는 경우, transaction_id를 통해 AND 필터링
    if entry_filters:
        transaction_ids = ProjectAccountingEntry.objects.filter(
            entry_filters
        ).values_list('transaction_id', flat=True).distinct()
        qs = qs.filter(transaction_id__in=transaction_ids)

    # search가 있는 경우, 거래 필드 또는 분개(계정명+하위계정 / 거래처) 매칭으로 AND 필터링
    if search:
        search_entry_q = Q(trader__icontains=search)
        matched_seed_ids = list(ProjectAccount.objects.filter(
            name__icontains=search, is_active=True
        ).values_list('id', flat=True))

        if matched_seed_ids:
            search_account_ids = _get_descendant_account_ids(matched_seed_ids)
            if search_account_ids:
                search_entry_q |= Q(account_id__in=search_account_ids)

        search_transaction_ids = ProjectAccountingEntry.objects.filter(
            search_entry_q
        ).values_list('transaction_id', flat=True).distinct()

        qs = qs.filter(
            Q(transaction_id__icontains=search) |
            Q(content__icontains=search) |
            Q(note__icontains=search) |
            Q(project__name__icontains=search) |
            Q(transaction_id__in=search_transaction_ids)
        )

    # 지연 평가(Lazy Evaluation) QuerySet 반환
    return qs.select_related(
        'project', 'bank_account', 'sort', 'creator'
    ).order_by('-deal_date', '-created_at')


def prefetch_project_transactions(instances, params=None):
    """지정된 거래 목록(instances)에 대해서만 분개를 수동 prefetch 맵핑합니다.

    검색/필터 조건에 의해 매칭된 거래(BankTransaction)의 전체 분개 내역이 온전히
    표시되도록, 거래에 속한 모든 분개를 가져옵니다.
    """
    transaction_ids = [t.transaction_id for t in instances if t.transaction_id]
    if not transaction_ids:
        for tx in instances:
            tx.prefetched_accounting_entries = []
        return instances

    # 페이징된 instances 대상 분개 쿼리 실행
    entries_qs = ProjectAccountingEntry.objects.filter(
        transaction_id__in=transaction_ids
    ).select_related(
        'project',
        'account',
        'account__parent',
        'account__parent__parent',
        'account__parent__parent__parent',
        'contract',
        'contract__contractor',
        'contract__contractor__contract',
        'contractor',
        'contractor__contract',
        'contract_payment',
        'contract_payment__contract',
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
