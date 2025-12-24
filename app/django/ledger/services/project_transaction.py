from django.db.models import Q
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

    # is_imprest 필터링 (bank_account의 is_imprest 속성 사용)
    is_imprest = params.get('is_imprest')
    if is_imprest is not None:
        is_imprest_bool = is_imprest.lower() in ('true', '1', 'yes') if isinstance(is_imprest, str) else bool(
            is_imprest)
        qs = qs.filter(bank_account__is_imprest=is_imprest_bool)

    # 회계분개 모델을 참조해야 하는 복합 필터링
    account_id = params.get('account')
    account_category = params.get('account_category')
    account_name = params.get('account_name')
    search = params.get('search')

    entry_filters = Q()

    if account_id:
        try:
            account = ProjectAccount.objects.get(pk=account_id)
            descendants = account.get_descendants(include_self=True)
            active_accounts = [acc.pk for acc in descendants if acc.is_active]
            entry_filters &= Q(account_id__in=active_accounts)
        except ProjectAccount.DoesNotExist:
            return ProjectBankTransaction.objects.none()

    if account_category:
        account_ids = ProjectAccount.objects.filter(
            category=account_category, is_active=True
        ).values_list('pk', flat=True)
        entry_filters &= Q(account_id__in=account_ids)

    if account_name:
        # 계정 이름으로 부분 일치 검색
        accounts = ProjectAccount.objects.filter(
            name__icontains=account_name, is_active=True
        )
        all_account_ids = []
        for acc in accounts:
            descendants = acc.get_descendants(include_self=True)
            active_descendants = [a.pk for a in descendants if a.is_active]
            all_account_ids.extend(active_descendants)

        account_ids = list(set(all_account_ids))
        entry_filters &= Q(account_id__in=account_ids)

    if search:
        # 계정 이름 검색
        accounts = ProjectAccount.objects.filter(name__icontains=search, is_active=True)
        all_account_ids = []
        for acc in accounts:
            descendants = acc.get_descendants(include_self=True)
            active_descendants = [a.pk for a in descendants if a.is_active]
            all_account_ids.extend(active_descendants)

        account_ids = list(set(all_account_ids))
        entry_filters |= Q(account_id__in=account_ids)

    # entry_filters가 있는 경우, transaction_id를 통해 필터링
    if entry_filters:
        transaction_ids = ProjectAccountingEntry.objects.filter(
            entry_filters
        ).values_list('transaction_id', flat=True).distinct()

        # search가 있는 경우 OR 조건, 없는 경우 AND 조건
        if search:
            qs = qs.filter(
                Q(transaction_id__icontains=search) |
                Q(content__icontains=search) |
                Q(note__icontains=search) |
                Q(project__name__icontains=search) |
                Q(transaction_id__in=transaction_ids)
            )
        else:
            qs = qs.filter(transaction_id__in=transaction_ids)
    elif search:
        # entry_filters는 없지만 search는 있는 경우
        qs = qs.filter(
            Q(transaction_id__icontains=search) |
            Q(content__icontains=search) |
            Q(note__icontains=search) |
            Q(project__name__icontains=search)
        )

    # 정렬 및 반환
    return qs.select_related(
        'project', 'bank_account', 'sort', 'creator'
    ).order_by('-deal_date', '-created_at')
