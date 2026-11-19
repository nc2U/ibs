"""본사 월별 자금 집계 서비스

단식부기(은행 입출금 1건 = 회계 분개 1건 이상) 구조에서 의미 있는 월간 자금 집계를 산출합니다.

집계 원칙
- 분류 기준은 계정 코드 대역이 아니라 '분개 계정의 category' + '은행 거래의 입금/출금(sort)' 조합입니다.
  (예: 4011 부가세 예수금/4012 선수금은 4000대 코드이지만 category=liability 이므로 '수익'이 아닌 '기타 수입')
- 수입: 수익(revenue 입금) / 수익 외 기타 수입(자산 회수·부채 증가·자본 유입 등)
- 지출: 비용(expense 출금) / 비용 외 기타 지출(자산 취득·부채 상환·자본 유출 등)
- 내부 자금이동(transfer)·거래취소(cancel)는 수입/지출 합계에서 제외하고 참고 항목으로 분리합니다.
- 은행 거래 금액과 분개 합계의 차이는 '미분류'로 분리하여 월간 잔고 증감과 1원 단위로 검산되게 합니다.
"""
import calendar
import datetime
from collections import defaultdict

from dateutil.relativedelta import relativedelta
from django.db.models import BigIntegerField, Case, F, Sum, When

from ledger.models import Affiliate, CompanyAccount, CompanyAccountingEntry, CompanyBankTransaction

SORT_IN = 1  # 입금
SORT_OUT = 2  # 출금

PERIOD_KEYS = ('prev', 'cur', 'ytd')


def _is_month_end(d: datetime.date) -> bool:
    return d.day == calendar.monthrange(d.year, d.month)[1]


def resolve_periods(from_date: datetime.date, to_date: datetime.date) -> dict:
    """당기(cur) / 전월 동기(prev) / 당해 누계(ytd) 기간을 계산합니다."""
    prev_from = from_date - relativedelta(months=1)
    prev_to = to_date - relativedelta(months=1)
    if _is_month_end(to_date):
        prev_to = prev_to.replace(day=calendar.monthrange(prev_to.year, prev_to.month)[1])
    return {
        'prev': (prev_from, prev_to),
        'cur': (from_date, to_date),
        'ytd': (datetime.date(to_date.year, 1, 1), to_date),
    }


def _periods_of(deal_date: datetime.date, periods: dict) -> list:
    return [key for key, (start, end) in periods.items() if start <= deal_date <= end]


def _classify(category: str, sort_id: int):
    """(구획, 소구획) 반환"""
    if category in ('transfer', 'cancel'):
        return category, 'in' if sort_id == SORT_IN else 'out'
    if sort_id == SORT_IN:
        return 'income', 'revenue' if category == 'revenue' else 'other'
    return 'expense', 'cost' if category == 'expense' else 'other'


def _zero():
    return {key: 0 for key in PERIOD_KEYS}


def _bank_balance(company_id: int, *, before: datetime.date = None, upto: datetime.date = None) -> int:
    qs = CompanyBankTransaction.objects.filter(company_id=company_id)
    if before:
        qs = qs.filter(deal_date__lt=before)
    if upto:
        qs = qs.filter(deal_date__lte=upto)
    agg = qs.aggregate(
        inc=Sum(Case(When(sort_id=SORT_IN, then=F('amount')), default=0, output_field=BigIntegerField())),
        out=Sum(Case(When(sort_id=SORT_OUT, then=F('amount')), default=0, output_field=BigIntegerField())),
    )
    return (agg['inc'] or 0) - (agg['out'] or 0)


def _build_groups(rows: dict, acc_map: dict, root_name_of) -> list:
    """계정별 행을 최상위 계정(대분류) 단위 그룹으로 묶습니다."""
    groups = {}
    for account_id, amounts in rows.items():
        acc = acc_map.get(account_id)
        if acc is None:
            continue
        group_name = root_name_of(account_id)
        group = groups.setdefault(group_name, {'name': group_name, 'rows': [], **_zero()})
        group['rows'].append({
            'account': account_id,
            'code': acc.code,
            'name': acc.name,
            'category': acc.category,
            **amounts,
        })
        for key in PERIOD_KEYS:
            group[key] += amounts[key]
    result = list(groups.values())
    for group in result:
        group['rows'].sort(key=lambda r: r['code'])
    result.sort(key=lambda g: g['rows'][0]['code'] if g['rows'] else '')
    return result


def _sum_groups(groups: list) -> dict:
    total = _zero()
    for group in groups:
        for key in PERIOD_KEYS:
            total[key] += group[key]
    return total


def build_company_monthly_summary(company_id: int, from_date: datetime.date, to_date: datetime.date) -> dict:
    periods = resolve_periods(from_date, to_date)
    query_start = min(start for start, _ in periods.values())

    tx_qs = CompanyBankTransaction.objects.filter(
        company_id=company_id, deal_date__gte=query_start, deal_date__lte=to_date)
    tx_map = {
        t['transaction_id']: t
        for t in tx_qs.values('transaction_id', 'sort_id', 'deal_date', 'amount')
    }
    entries = CompanyAccountingEntry.objects.filter(
        company_id=company_id,
        transaction_id__in=tx_qs.values('transaction_id'),
    ).values('transaction_id', 'account_id', 'amount', 'affiliate_id')

    acc_map = {a.pk: a for a in CompanyAccount.objects.only('id', 'code', 'name', 'category', 'parent_id')}

    root_cache = {}

    def root_name_of(account_id):
        if account_id in root_cache:
            return root_cache[account_id]
        acc = acc_map.get(account_id)
        visited = set()
        while acc is not None and acc.parent_id and acc.pk not in visited:
            visited.add(acc.pk)
            acc = acc_map.get(acc.parent_id)
        name = acc.name if acc else '기타'
        root_cache[account_id] = name
        return name

    sections = {
        ('income', 'revenue'): defaultdict(_zero),
        ('income', 'other'): defaultdict(_zero),
        ('expense', 'cost'): defaultdict(_zero),
        ('expense', 'other'): defaultdict(_zero),
    }
    side_totals = {  # 참고 항목: transfer / cancel
        ('transfer', 'in'): _zero(), ('transfer', 'out'): _zero(),
        ('cancel', 'in'): _zero(), ('cancel', 'out'): _zero(),
    }
    entry_sum_by_tx = defaultdict(int)
    affiliate_rows = defaultdict(lambda: {'cur': defaultdict(int), 'ytd': defaultdict(int)})

    for entry in entries:
        tx = tx_map.get(entry['transaction_id'])
        if tx is None:
            continue
        acc = acc_map.get(entry['account_id'])
        if acc is None:
            continue
        amount = entry['amount'] or 0
        entry_sum_by_tx[entry['transaction_id']] += amount
        keys = _periods_of(tx['deal_date'], periods)
        section, sub = _classify(acc.category, tx['sort_id'])

        if section in ('transfer', 'cancel'):
            for key in keys:
                side_totals[(section, sub)][key] += amount
        else:
            for key in keys:
                sections[(section, sub)][entry['account_id']][key] += amount

        if entry['affiliate_id'] and section not in ('transfer', 'cancel'):
            if acc.category == 'asset':
                kind = 'lend' if tx['sort_id'] == SORT_OUT else 'collect'
            elif acc.category == 'liability':
                kind = 'borrow' if tx['sort_id'] == SORT_IN else 'repay'
            else:
                kind = 'other_in' if tx['sort_id'] == SORT_IN else 'other_out'
            for key in keys:
                if key in ('cur', 'ytd'):
                    affiliate_rows[entry['affiliate_id']][key][kind] += amount

    # 미분류(은행 거래 금액 - 분개 합계), 은행 총 입출금
    unclassified = {'in': _zero(), 'out': _zero()}
    bank_flow = {'in': _zero(), 'out': _zero()}
    for tx_id, tx in tx_map.items():
        direction = 'in' if tx['sort_id'] == SORT_IN else 'out'
        diff = (tx['amount'] or 0) - entry_sum_by_tx.get(tx_id, 0)
        for key in _periods_of(tx['deal_date'], periods):
            bank_flow[direction][key] += tx['amount'] or 0
            if diff:
                unclassified[direction][key] += diff

    revenue_groups = _build_groups(sections[('income', 'revenue')], acc_map, root_name_of)
    income_other_groups = _build_groups(sections[('income', 'other')], acc_map, root_name_of)
    cost_groups = _build_groups(sections[('expense', 'cost')], acc_map, root_name_of)
    expense_other_groups = _build_groups(sections[('expense', 'other')], acc_map, root_name_of)

    revenue_total = _sum_groups(revenue_groups)
    income_other_total = _sum_groups(income_other_groups)
    cost_total = _sum_groups(cost_groups)
    expense_other_total = _sum_groups(expense_other_groups)

    income_total = {k: revenue_total[k] + income_other_total[k] for k in PERIOD_KEYS}
    expense_total = {k: cost_total[k] + expense_other_total[k] for k in PERIOD_KEYS}

    # 관계회사/프로젝트별 자금 이동
    affiliate_list = []
    if affiliate_rows:
        aff_objs = Affiliate.objects.filter(pk__in=affiliate_rows.keys()).select_related('company', 'project')
        for aff in aff_objs:
            data = affiliate_rows[aff.pk]
            label = str(aff)
            row = {'affiliate': aff.pk, 'label': label, 'sort': aff.sort}
            for period in ('cur', 'ytd'):
                d = data[period]
                inflow = d['collect'] + d['borrow'] + d['other_in']
                outflow = d['lend'] + d['repay'] + d['other_out']
                row[period] = {
                    'lend': d['lend'], 'collect': d['collect'],
                    'borrow': d['borrow'], 'repay': d['repay'],
                    'other_in': d['other_in'], 'other_out': d['other_out'],
                    'net': inflow - outflow,
                }
            affiliate_list.append(row)
        affiliate_list.sort(key=lambda r: r['label'])

    opening_balance = _bank_balance(company_id, before=from_date)
    closing_balance = _bank_balance(company_id, upto=to_date)

    return {
        'company': company_id,
        'from_date': from_date.isoformat(),
        'to_date': to_date.isoformat(),
        'periods': {k: {'from': s.isoformat(), 'to': e.isoformat()} for k, (s, e) in periods.items()},
        'opening_balance': opening_balance,
        'closing_balance': closing_balance,
        'income': {
            'revenue': {'groups': revenue_groups, 'total': revenue_total},
            'other': {'groups': income_other_groups, 'total': income_other_total},
            'total': income_total,
        },
        'expense': {
            'cost': {'groups': cost_groups, 'total': cost_total},
            'other': {'groups': expense_other_groups, 'total': expense_other_total},
            'total': expense_total,
        },
        'operating_net': {k: revenue_total[k] - cost_total[k] for k in PERIOD_KEYS},
        'net': {k: income_total[k] - expense_total[k] for k in PERIOD_KEYS},
        'transfer': {'in': side_totals[('transfer', 'in')], 'out': side_totals[('transfer', 'out')]},
        'cancel': {'in': side_totals[('cancel', 'in')], 'out': side_totals[('cancel', 'out')]},
        'unclassified': unclassified,
        'bank_flow': bank_flow,
        'affiliates': affiliate_list,
    }
