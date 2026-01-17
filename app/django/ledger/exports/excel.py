"""Ledger Excel Export Views

원장 관련 Excel 내보내기 뷰들
"""
import datetime
from collections import defaultdict

import xlwt
from dateutil.relativedelta import relativedelta
from django.db.models import Q, Sum, When, F, PositiveBigIntegerField, Case
from django.http import HttpResponse

from _excel.mixins import ExcelExportMixin, XlwtStyleMixin
from company.models import Company
from ledger.models import CompanyBankTransaction, CompanyAccountingEntry, ProjectBankTransaction, \
    ProjectAccountingEntry, ProjectAccount
from ledger.services.company_transaction import get_company_transactions
from ledger.services.project_transaction import get_project_transactions
from project.models import Project, ProjectOutBudget

TODAY = datetime.date.today().strftime('%Y-%m-%d')


class ExportLedgerBalanceByAcc(ExcelExportMixin):
    """본사 계좌별 잔고 내역 (원장 기반)"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('본사_계좌별_자금현황')

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)
        number_format = self.create_number_format(workbook)
        center_format = self.create_center_format(workbook)
        left_format = self.create_left_format(workbook)
        sume_format = self.create_sum_format(workbook)

        # data start --------------------------------------------- #
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')
        date = request.GET.get('date') or TODAY

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.write(row_num, 0, com_name + ' 계좌별 자금현황', title_format)
        row_num += 1

        # 2. Header
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, 6, date + ' 현재', workbook.add_format({'align': 'right'}))
        row_num += 1

        # 3. Header
        worksheet.set_column(0, 0, 10)
        worksheet.merge_range(row_num, 0, row_num, 2, '계좌 구분', h_format)
        worksheet.set_column(1, 1, 30)
        worksheet.set_column(2, 2, 30)
        worksheet.set_column(3, 3, 20)
        worksheet.write(row_num, 3, '전일잔고', h_format)
        worksheet.set_column(4, 4, 20)
        worksheet.write(row_num, 4, '금일입금(증가)', h_format)
        worksheet.set_column(5, 5, 20)
        worksheet.write(row_num, 5, '금일출금(감소)', h_format)
        worksheet.set_column(6, 6, 20)
        worksheet.write(row_num, 6, '금일잔고', h_format)

        # 4. Contents - CompanyBankTransaction 기반 데이터 조회 (Vue API와 동일한 로직)
        qs = CompanyBankTransaction.objects.filter(deal_date__lte=date).order_by('bank_account')
        if company:
            qs = qs.filter(company_id=company.pk)

        balance_set = qs.values(
            bank_acc=F('bank_account__alias_name'),
            bank_num=F('bank_account__number')
        ).annotate(
            # 누적 합계 (Vue API와 동일한 로직)
            inc_sum=Sum(Case(
                When(sort_id=1, then=F('amount')),  # 1 = 입금
                default=0
            )),
            out_sum=Sum(Case(
                When(sort_id=2, then=F('amount')),  # 2 = 출금
                default=0
            )),
            # 당일 합계 (Vue API와 동일한 로직)
            date_inc=Sum(Case(
                When(sort_id=1, deal_date=date, then=F('amount')),
                default=0
            )),
            date_out=Sum(Case(
                When(sort_id=2, deal_date=date, then=F('amount')),
                default=0
            ))
        )

        total_inc = 0
        total_out = 0
        total_inc_sum = 0
        total_out_sum = 0

        # Turn off the warnings:
        worksheet.ignore_errors({'number_stored_as_text': 'B:C'})

        for row, balance in enumerate(balance_set):
            row_num += 1
            inc_sum = balance['inc_sum'] if balance['inc_sum'] else 0
            out_sum = balance['out_sum'] if balance['out_sum'] else 0
            date_inc = balance['date_inc'] if balance['date_inc'] else 0
            date_out = balance['date_out'] if balance['date_out'] else 0

            total_inc += date_inc
            total_out += date_out
            total_inc_sum += inc_sum
            total_out_sum += out_sum

            for col in range(7):
                if col == 0 and row == 0:
                    worksheet.write(row_num, col, '현금', center_format)
                if col == 0 and row == 1:
                    worksheet.merge_range(row_num, col, balance_set.count() + 2, col, '보통예금', center_format)
                if col == 1:
                    worksheet.write(row_num, col, balance['bank_acc'], left_format)
                if col == 2:
                    worksheet.write(row_num, col, balance['bank_num'], left_format)
                if col == 3:
                    worksheet.write(row_num, col, inc_sum - out_sum - date_inc + date_out, number_format)
                if col == 4:
                    worksheet.write(row_num, col, date_inc, number_format)
                if col == 5:
                    worksheet.write(row_num, col, date_out, number_format)
                if col == 6:
                    worksheet.write(row_num, col, inc_sum - out_sum, number_format)

        # 5. Sum row
        row_num += 1
        worksheet.merge_range(row_num, 0, row_num, 2, '현금성 자산 계', sume_format)
        worksheet.write(row_num, 3, total_inc_sum - total_out_sum - total_inc + total_out, sume_format)
        worksheet.write(row_num, 4, total_inc, sume_format)
        worksheet.write(row_num, 5, total_out, sume_format)
        worksheet.write(row_num, 6, total_inc_sum - total_out_sum, sume_format)

        # data end ----------------------------------------------- #

        # Close the workbook before sending the data.
        filename = request.GET.get('filename')
        filename = f'{filename}-{date}' if filename else f'balance-{date}'
        return ExcelExportMixin.create_response(output, workbook, filename)


class ExportLedgerDateCashbook(ExcelExportMixin):
    """본사 일별 입출금 내역 (원장 기반)"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('당일_입출금내역')

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)
        number_format = self.create_number_format(workbook)
        center_format = self.create_center_format(workbook)
        left_format = self.create_left_format(workbook)
        sum_format = self.create_sum_format(workbook)

        # data start --------------------------------------------- #
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')
        date = request.GET.get('date') or TODAY

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.write(row_num, 0, com_name + ' 당일 입출금내역 [' + date + ' 기준]', title_format)
        row_num += 1

        # 2. Header
        worksheet.set_row(row_num, 18)
        row_num += 1

        # 3. Header - 10 columns: Bank Transaction (6) + Classification (4)
        worksheet.set_column(0, 0, 12)
        worksheet.write(row_num, 0, '일시', h_format)
        worksheet.set_column(1, 1, 20)
        worksheet.write(row_num, 1, '메모', h_format)
        worksheet.set_column(2, 2, 20)
        worksheet.write(row_num, 2, '계좌', h_format)
        worksheet.set_column(3, 3, 25)
        worksheet.write(row_num, 3, '적요', h_format)
        worksheet.set_column(4, 4, 15)
        worksheet.write(row_num, 4, '입금액', h_format)
        worksheet.set_column(5, 5, 15)
        worksheet.write(row_num, 5, '출금액', h_format)
        worksheet.set_column(6, 6, 20)
        worksheet.write(row_num, 6, '계정', h_format)
        worksheet.set_column(7, 7, 15)
        worksheet.write(row_num, 7, '거래처', h_format)
        worksheet.set_column(8, 8, 15)
        worksheet.write(row_num, 8, '분류금액', h_format)
        worksheet.set_column(9, 9, 15)
        worksheet.write(row_num, 9, '증빙', h_format)

        # 4. Contents - CompanyBankTransaction 기반 데이터 조회 (Vue API daily_transactions와 동일한 로직)
        transactions = CompanyBankTransaction.objects.filter(
            company_id=company.pk,
            deal_date=date
        ).select_related(
            'bank_account', 'sort', 'creator'
        ).order_by('sort_id', 'created_at')

        # 수동으로 prefetch 하기 (Vue API와 동일)
        transaction_ids = [t.transaction_id for t in transactions]
        entries_map = defaultdict(list)

        if transaction_ids:
            # 관련된 모든 회계 분개를 한 번의 쿼리로 가져오기
            accounting_entries = CompanyAccountingEntry.objects.filter(
                transaction_id__in=transaction_ids
            ).select_related('account')

            # transaction_id를 키로 하는 딕셔너리 생성
            for entry in accounting_entries:
                entries_map[entry.transaction_id].append(entry)

        inc_sum = 0
        out_sum = 0

        # Process each transaction (Vue API와 동일한 로직)
        for trans in transactions:
            entries = entries_map.get(trans.transaction_id, [])

            # 합계 계산
            if trans.sort_id == 1:  # 입금
                inc_sum += trans.amount or 0
            elif trans.sort_id == 2:  # 출금
                out_sum += trans.amount or 0

            if not entries:  # 거래는 있으나 분개가 없는 경우
                row_num += 1
                worksheet.write(row_num, 0, trans.deal_date.strftime('%Y-%m-%d'), center_format)
                worksheet.write(row_num, 1, trans.note or '', left_format)
                worksheet.write(row_num, 2, trans.bank_account.alias_name if trans.bank_account else '', left_format)
                worksheet.write(row_num, 3, trans.content or '', left_format)
                worksheet.write(row_num, 4, trans.amount if trans.sort_id == 1 else 0, number_format)
                worksheet.write(row_num, 5, trans.amount if trans.sort_id == 2 else 0, number_format)
                worksheet.write(row_num, 6, '', left_format)
                worksheet.write(row_num, 7, '', left_format)
                worksheet.write(row_num, 8, '', number_format)
                worksheet.write(row_num, 9, '', center_format)
            elif len(entries) == 1:  # 단일 분개
                entry = entries[0]
                row_num += 1
                # Bank transaction columns
                worksheet.write(row_num, 0, trans.deal_date.strftime('%Y-%m-%d'), center_format)
                worksheet.write(row_num, 1, trans.note or '', left_format)
                worksheet.write(row_num, 2, trans.bank_account.alias_name if trans.bank_account else '', left_format)
                worksheet.write(row_num, 3, trans.content or '', left_format)
                worksheet.write(row_num, 4, trans.amount if trans.sort_id == 1 else 0, number_format)
                worksheet.write(row_num, 5, trans.amount if trans.sort_id == 2 else 0, number_format)
                # Classification columns
                worksheet.write(row_num, 6, entry.account.name if entry.account else '', left_format)
                worksheet.write(row_num, 7, entry.trader or '', left_format)
                worksheet.write(row_num, 8, entry.amount or 0, number_format)
                worksheet.write(row_num, 9, entry.get_evidence_type_display() or '', center_format)
            else:  # 복수 분개
                for i, acc_entry in enumerate(entries):
                    row_num += 1
                    if i == 0:
                        # Bank transaction columns - only on the first row
                        worksheet.write(row_num, 0, trans.deal_date.strftime('%Y-%m-%d'), center_format)
                        worksheet.write(row_num, 1, trans.note or '', left_format)
                        worksheet.write(row_num, 2, trans.bank_account.alias_name if trans.bank_account else '',
                                        left_format)
                        worksheet.write(row_num, 3, trans.content or '', left_format)
                        worksheet.write(row_num, 4, trans.amount if trans.sort_id == 1 else 0, number_format)
                        worksheet.write(row_num, 5, trans.amount if trans.sort_id == 2 else 0, number_format)
                    else:
                        # Empty bank transaction columns for subsequent rows
                        worksheet.write(row_num, 0, '', center_format)
                        worksheet.write(row_num, 1, '', left_format)
                        worksheet.write(row_num, 2, '', left_format)
                        worksheet.write(row_num, 3, '', left_format)
                        worksheet.write(row_num, 4, '', number_format)
                        worksheet.write(row_num, 5, '', number_format)

                    # Classification columns are always written
                    worksheet.write(row_num, 6, acc_entry.account.name if acc_entry.account else '', left_format)
                    worksheet.write(row_num, 7, acc_entry.trader or '', left_format)
                    worksheet.write(row_num, 8, acc_entry.amount or 0, number_format)
                    worksheet.write(row_num, 9, acc_entry.get_evidence_type_display() or '', center_format)

        # 5. Sum row
        row_num += 1
        worksheet.merge_range(row_num, 0, row_num, 3, '합계', sum_format)
        worksheet.write(row_num, 4, inc_sum, sum_format)
        worksheet.write(row_num, 5, out_sum, sum_format)
        worksheet.write(row_num, 6, '', sum_format)
        worksheet.write(row_num, 7, '', sum_format)
        worksheet.write(row_num, 8, '', sum_format)
        worksheet.write(row_num, 9, '', sum_format)

        # data end ----------------------------------------------- #

        # Close the workbook before sending the data.
        filename = request.GET.get('filename')
        filename = f'{filename}-{date}' if filename else f'date-transactions-{date}'
        return ExcelExportMixin.create_response(output, workbook, filename)


def export_com_transaction_xls(request):
    """본사 입출금 내역 (공용 서비스 함수 사용)"""
    # 서비스 함수를 직접 호출하므로 ViewSet 관련 import는 더 이상 필요 없음

    filename = request.GET.get('filename')
    filename = f'{filename}-{TODAY}' if filename else f'cashbook-{TODAY}'
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}.xls'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('본사_입출금_내역')

    # --- 데이터 조회 로직 (공용 서비스 함수 직접 호출) ---
    # request.GET을 직접 전달하여 모든 필터 파라미터를 서비스 함수가 처리하도록 함
    obj_list = get_company_transactions(request.GET)
    obj_list = obj_list.order_by('deal_date', 'created_at')
    # -----------------------------------------

    # --- N+1 문제 해결을 위한 수동 Prefetch ---
    transaction_ids = [t.transaction_id for t in obj_list]
    if transaction_ids:
        accounting_entries = CompanyAccountingEntry.objects.filter(
            transaction_id__in=transaction_ids
        ).select_related('account')

        entries_map = defaultdict(list)
        for entry in accounting_entries:
            entries_map[entry.transaction_id].append(entry)

        for transaction in obj_list:
            transaction.prefetched_entries = entries_map.get(transaction.transaction_id, [])
    # ------------------------------------

    company = Company.objects.get(pk=request.GET.get('company'))
    com_name = company.name.replace('주식회사 ', '(주)')

    # Sheet Title, first row
    row_num = 0

    style = xlwt.XFStyle()
    style.font.bold = True
    style.font.height = 300
    style.alignment.vert = style.alignment.VERT_CENTER

    ws.write(row_num, 0, com_name + ' 입출금 내역', style)
    ws.row(0).height_mismatch = True
    ws.row(0).height = 38 * 20

    # Column definitions
    columns = [
        '일시', '메모', '계좌', '적요', '입금액', '출금액',
        '계정', '거래처', '분류금액', '증빙'
    ]

    # Column width settings
    ws.col(0).width = 110 * 30
    ws.col(1).width = 100 * 30
    ws.col(2).width = 170 * 30
    ws.col(3).width = 180 * 30
    ws.col(4).width = 110 * 30
    ws.col(5).width = 110 * 30
    ws.col(6).width = 160 * 30
    ws.col(7).width = 120 * 30
    ws.col(8).width = 110 * 30
    ws.col(9).width = 100 * 30

    # Sheet header, second row
    row_num = 1

    header_style = xlwt.XFStyle()
    header_style.font.bold = True
    header_style.borders.left = 1
    header_style.borders.right = 1
    header_style.borders.top = 1
    header_style.borders.bottom = 1
    header_style.pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    header_style.pattern.pattern_fore_colour = xlwt.Style.colour_map['silver_ega']
    header_style.alignment.vert = header_style.alignment.VERT_CENTER
    header_style.alignment.horz = header_style.alignment.HORZ_CENTER

    for col_num, col_name in enumerate(columns):
        ws.write(row_num, col_num, col_name, header_style)

    # Sheet body, remaining rows
    styles = XlwtStyleMixin.create_xlwt_styles()

    for trans in obj_list:
        entries = getattr(trans, 'prefetched_entries', [])
        if not entries:  # 거래는 있으나 분개가 없는 경우
            row_num += 1
            ws.write(row_num, 0, trans.deal_date.strftime('%Y-%m-%d'), styles['date'])
            ws.write(row_num, 1, trans.note or '', styles['default'])
            ws.write(row_num, 2, trans.bank_account.alias_name if trans.bank_account else '', styles['default'])
            ws.write(row_num, 3, trans.content or '', styles['default'])
            ws.write(row_num, 4, trans.amount if trans.sort.pk == 1 else 0, styles['amount'])
            ws.write(row_num, 5, trans.amount if trans.sort.pk == 2 else 0, styles['amount'])
            for i in range(6, 10):
                ws.write(row_num, i, '', styles['default'])
        elif len(entries) == 1:
            entry = entries[0]
            row_num += 1
            # Bank transaction columns
            ws.write(row_num, 0, trans.deal_date.strftime('%Y-%m-%d'), styles['date'])
            ws.write(row_num, 1, trans.note or '', styles['default'])
            ws.write(row_num, 2, trans.bank_account.alias_name if trans.bank_account else '', styles['default'])
            ws.write(row_num, 3, trans.content or '', styles['default'])
            ws.write(row_num, 4, trans.amount if trans.sort.pk == 1 else 0, styles['amount'])
            ws.write(row_num, 5, trans.amount if trans.sort.pk == 2 else 0, styles['amount'])
            # Classification columns
            ws.write(row_num, 6, entry.account.name if entry.account else '', styles['default'])
            ws.write(row_num, 7, entry.trader or '', styles['default'])
            ws.write(row_num, 8, entry.amount or 0, styles['amount'])
            ws.write(row_num, 9, entry.get_evidence_type_display() or '', styles['default'])
        else:
            for i, acc_entry in enumerate(entries):
                row_num += 1
                if i == 0:
                    # Bank transaction columns - only on the first row
                    ws.write(row_num, 0, trans.deal_date.strftime('%Y-%m-%d'), styles['date'])
                    ws.write(row_num, 1, trans.note or '', styles['default'])
                    ws.write(row_num, 2, trans.bank_account.alias_name if trans.bank_account else '', styles['default'])
                    ws.write(row_num, 3, trans.content or '', styles['default'])
                    ws.write(row_num, 4, trans.amount if trans.sort.pk == 1 else 0, styles['amount'])
                    ws.write(row_num, 5, trans.amount if trans.sort.pk == 2 else 0, styles['amount'])

                # Classification columns are always written
                ws.write(row_num, 6, acc_entry.account.name if acc_entry.account else '', styles['default'])
                ws.write(row_num, 7, acc_entry.trader or '', styles['default'])
                ws.write(row_num, 8, acc_entry.amount or 0, styles['amount'])
                ws.write(row_num, 9, acc_entry.get_evidence_type_display() or '', styles['default'])

    wb.save(response)
    return response


class ExportProjectLedgerBalance(ExcelExportMixin):
    """프로젝트 계좌별 잔고 내역"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('계좌별_자금현황')

        # 데이터 조회
        project = Project.objects.get(pk=request.GET.get('project'))
        date = request.GET.get('date') or TODAY

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)
        number_format = self.create_number_format(workbook)
        center_format = self.create_center_format(workbook)
        left_format = self.create_left_format(workbook)

        # 1. 제목
        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.write(row_num, 0, f'{project} 계좌별 자금현황', title_format)
        row_num += 1

        # 2. 날짜
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, 6, f'{date} 현재', workbook.add_format({'align': 'right'}))
        row_num += 1

        # 3. 헤더
        worksheet.set_column(0, 0, 10)
        worksheet.merge_range(row_num, 0, row_num, 2, '계좌 구분', h_format)
        worksheet.set_column(1, 1, 30)
        worksheet.set_column(2, 2, 20)
        worksheet.set_column(3, 3, 20)
        worksheet.write(row_num, 3, '전일잔고', h_format)
        worksheet.set_column(4, 4, 20)
        worksheet.write(row_num, 4, '금일입금(증가)', h_format)
        worksheet.set_column(5, 5, 20)
        worksheet.write(row_num, 5, '금일출금(감소)', h_format)
        worksheet.set_column(6, 6, 20)
        worksheet.write(row_num, 6, '금일잔고', h_format)
        row_num += 1

        # 4. 데이터 조회
        balance_set = self._get_balance_data(date)
        worksheet.ignore_errors({'number_stored_as_text': 'B:C'})

        # 5. 데이터 작성
        totals = {'inc': 0, 'out': 0, 'inc_sum': 0, 'out_sum': 0}
        balance_list = list(balance_set)

        for row_idx, balance in enumerate(balance_list):
            inc_sum = balance['inc_sum'] or 0
            out_sum = balance['out_sum'] or 0
            date_inc = balance['date_inc'] or 0
            date_out = balance['date_out'] or 0

            totals['inc'] += date_inc
            totals['out'] += date_out
            totals['inc_sum'] += inc_sum
            totals['out_sum'] += out_sum

            # 첫 행에만 '보통예금' 병합
            if row_idx == 0:
                worksheet.merge_range(row_num, 0, row_num + len(balance_list) - 1, 0, '보통예금', center_format)

            worksheet.write(row_num, 1, balance['bank_acc'], left_format)
            worksheet.write(row_num, 2, balance['bank_num'], left_format)
            worksheet.write(row_num, 3, inc_sum - out_sum - date_inc + date_out, number_format)
            worksheet.write(row_num, 4, date_inc, number_format)
            worksheet.write(row_num, 5, date_out, number_format)
            worksheet.write(row_num, 6, inc_sum - out_sum, number_format)
            row_num += 1

        # 6. 합계 행
        worksheet.merge_range(row_num, 0, row_num, 2, '현금성 자산 계', center_format)
        worksheet.write(row_num, 3, totals['inc_sum'] - totals['out_sum'] - totals['inc'] + totals['out'],
                        number_format)
        worksheet.write(row_num, 4, totals['inc'], number_format)
        worksheet.write(row_num, 5, totals['out'], number_format)
        worksheet.write(row_num, 6, totals['inc_sum'] - totals['out_sum'], number_format)

        # 응답 생성
        filename = request.GET.get('filename') or 'project-balance'
        filename = f'{filename}-{date}'
        return self.create_response(output, workbook, filename)

    @staticmethod
    def _get_balance_data(date):
        """잔고 데이터 조회"""
        qs = ProjectBankTransaction.objects.filter(
            bank_account__directpay=False,
            deal_date__lte=date
        ).order_by('bank_account')

        return qs.annotate(
            bank_acc=F('bank_account__alias_name'),
            bank_num=F('bank_account__number')
        ).values('bank_acc', 'bank_num').annotate(
            inc_sum=Sum(Case(When(sort_id=1, then=F('amount')), default=0)),
            out_sum=Sum(Case(When(sort_id=2, then=F('amount')), default=0)),
            date_inc=Sum(Case(When(sort_id=1, deal_date=date, then=F('amount')), default=0)),
            date_out=Sum(Case(When(sort_id=2, deal_date=date, then=F('amount')), default=0))
        )


class ExportProjectLedgerDateCashbook(ExcelExportMixin):
    """프로젝트 일별 입출금 내역"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('당일_입출금내역')

        # data start --------------------------------------------- #

        project = Project.objects.get(pk=request.GET.get('project'))
        date = request.GET.get('date') or TODAY

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)
        number_format = self.create_number_format(workbook)
        center_format = self.create_center_format(workbook)
        left_format = self.create_left_format(workbook)

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.write(row_num, 0, str(project) + ' 당일 입출금내역 [' + date + ' 기준]', title_format)
        row_num += 1

        # 2. Date
        worksheet.set_row(row_num, 18)
        # worksheet.write(row_num, 6, date + ' 현재', workbook.add_format({'align': 'right'}))
        row_num += 1

        # 3. Header - 열 구조 변경: 은행거래 내역(6열) + 분류 내역(4열)
        worksheet.set_column(0, 0, 12)
        worksheet.write(row_num, 0, '일시', h_format)
        worksheet.set_column(1, 1, 20)
        worksheet.write(row_num, 1, '메모', h_format)
        worksheet.set_column(2, 2, 20)
        worksheet.write(row_num, 2, '계좌', h_format)
        worksheet.set_column(3, 3, 25)
        worksheet.write(row_num, 3, '적요', h_format)
        worksheet.set_column(4, 4, 15)
        worksheet.write(row_num, 4, '입금액', h_format)
        worksheet.set_column(5, 5, 15)
        worksheet.write(row_num, 5, '출금액', h_format)
        worksheet.set_column(6, 6, 20)
        worksheet.write(row_num, 6, '계정', h_format)
        worksheet.set_column(7, 7, 15)
        worksheet.write(row_num, 7, '거래처', h_format)
        worksheet.set_column(8, 8, 15)
        worksheet.write(row_num, 8, '분류금액', h_format)
        worksheet.set_column(9, 9, 15)
        worksheet.write(row_num, 9, '증빙', h_format)

        # 4. Contents - ProjectBankTransaction 기반으로 변경 (회사 클래스와 동일한 패턴)
        transactions = ProjectBankTransaction.objects.filter(
            project_id=project.pk,
            deal_date=date
        ).select_related(
            'bank_account', 'sort', 'creator'
        ).order_by('sort_id', 'created_at')

        # 수동으로 prefetch 하기 (회사 클래스와 동일)
        transaction_ids = [t.transaction_id for t in transactions]
        entries_map = defaultdict(list)

        if transaction_ids:
            # 관련된 모든 회계 분개를 한 번의 쿼리로 가져오기
            accounting_entries = ProjectAccountingEntry.objects.filter(
                transaction_id__in=transaction_ids
            ).select_related('account')

            # transaction_id를 키로 하는 딕셔너리 생성
            for entry in accounting_entries:
                entries_map[entry.transaction_id].append(entry)

        inc_sum = 0
        out_sum = 0

        # Process each transaction (회사 클래스와 동일한 로직)
        for trans in transactions:
            entries = entries_map.get(trans.transaction_id, [])

            # 합계 계산
            if trans.sort_id == 1:  # 입금
                inc_sum += trans.amount or 0
            elif trans.sort_id == 2:  # 출금
                out_sum += trans.amount or 0

            if not entries:  # 거래는 있으나 분개가 없는 경우
                row_num += 1
                worksheet.write(row_num, 0, trans.deal_date.strftime('%Y-%m-%d'), center_format)
                worksheet.write(row_num, 1, trans.note or '', left_format)
                worksheet.write(row_num, 2, trans.bank_account.alias_name if trans.bank_account else '', left_format)
                worksheet.write(row_num, 3, trans.content or '', left_format)
                worksheet.write(row_num, 4, trans.amount if trans.sort_id == 1 else 0, number_format)
                worksheet.write(row_num, 5, trans.amount if trans.sort_id == 2 else 0, number_format)
                worksheet.write(row_num, 6, '', left_format)  # 계정 (empty)
                worksheet.write(row_num, 7, '', left_format)  # 거래처 (empty)
                worksheet.write(row_num, 8, '', number_format)  # 분류금액 (empty)
                worksheet.write(row_num, 9, '', center_format)  # 증빙 (empty)
            elif len(entries) == 1:  # 단일 분개
                entry = entries[0]
                row_num += 1
                # Bank transaction columns
                worksheet.write(row_num, 0, trans.deal_date.strftime('%Y-%m-%d'), center_format)
                worksheet.write(row_num, 1, trans.note or '', left_format)
                worksheet.write(row_num, 2, trans.bank_account.alias_name if trans.bank_account else '', left_format)
                worksheet.write(row_num, 3, trans.content or '', left_format)
                worksheet.write(row_num, 4, trans.amount if trans.sort_id == 1 else 0, number_format)
                worksheet.write(row_num, 5, trans.amount if trans.sort_id == 2 else 0, number_format)
                # Classification columns
                worksheet.write(row_num, 6, entry.account.name if entry.account else '', left_format)
                worksheet.write(row_num, 7, entry.trader or '', left_format)
                worksheet.write(row_num, 8, entry.amount or 0, number_format)
                worksheet.write(row_num, 9, entry.get_evidence_type_display() or '', center_format)
            else:  # 복수 분개
                for i, acc_entry in enumerate(entries):
                    row_num += 1
                    if i == 0:
                        # Bank transaction columns - only on the first row
                        worksheet.write(row_num, 0, trans.deal_date.strftime('%Y-%m-%d'), center_format)
                        worksheet.write(row_num, 1, trans.note or '', left_format)
                        worksheet.write(row_num, 2, trans.bank_account.alias_name if trans.bank_account else '',
                                        left_format)
                        worksheet.write(row_num, 3, trans.content or '', left_format)
                        worksheet.write(row_num, 4, trans.amount if trans.sort_id == 1 else 0, number_format)
                        worksheet.write(row_num, 5, trans.amount if trans.sort_id == 2 else 0, number_format)
                    else:
                        # Empty bank transaction columns for subsequent rows
                        worksheet.write(row_num, 0, '', center_format)
                        worksheet.write(row_num, 1, '', left_format)
                        worksheet.write(row_num, 2, '', left_format)
                        worksheet.write(row_num, 3, '', left_format)
                        worksheet.write(row_num, 4, '', number_format)
                        worksheet.write(row_num, 5, '', number_format)

                    # Classification columns are always written
                    worksheet.write(row_num, 6, acc_entry.account.name if acc_entry.account else '', left_format)
                    worksheet.write(row_num, 7, acc_entry.trader or '', left_format)
                    worksheet.write(row_num, 8, acc_entry.amount or 0, number_format)
                    worksheet.write(row_num, 9, acc_entry.get_evidence_type_display() or '', center_format)

        # 5. Sum row
        row_num += 1
        h_format.set_num_format(41)
        worksheet.merge_range(row_num, 0, row_num, 3, '합계', h_format)
        worksheet.write(row_num, 4, inc_sum, h_format)
        worksheet.write(row_num, 5, out_sum, h_format)
        worksheet.write(row_num, 6, '', h_format)
        worksheet.write(row_num, 7, '', h_format)
        worksheet.write(row_num, 8, '', h_format)
        worksheet.write(row_num, 9, '', h_format)

        # data end ----------------------------------------------- #

        # Close the workbook before sending the data.
        filename = request.GET.get('filename')
        filename = f'{filename}-{date}' if filename else f'project-date-cashbook-{date}'
        return ExcelExportMixin.create_response(output, workbook, filename)


class ExportLedgerBudgetExecutionStatus(ExcelExportMixin):
    """프로젝트 예산 대비 현황 (ledger 기반)"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('예산집행_현황')

        # data start --------------------------------------------- #
        project = Project.objects.get(pk=request.GET.get('project'))
        date = request.GET.get('date') or TODAY
        revised = request.GET.get('revised')
        is_revised = int(revised) if revised in ('0', '1') else 0

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)
        number_format = self.create_number_format(workbook)
        center_format = self.create_center_format(workbook)
        left_format = self.create_left_format(workbook)

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.write(row_num, 0, str(project) + ' 예산집행 현황', title_format)
        row_num += 1

        # 2. Header
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, 8, date + ' 현재', workbook.add_format({'align': 'right'}))
        row_num += 1

        # 3. Header
        worksheet.set_column(0, 0, 10)
        worksheet.set_column(1, 1, 10)
        worksheet.set_column(2, 2, 12)
        worksheet.set_column(3, 3, 18)
        worksheet.merge_range(row_num, 0, row_num, 3, '구분', h_format)
        worksheet.set_column(4, 4, 20)
        budget_str = '현황 예산' if is_revised else '기초 예산'
        worksheet.write(row_num, 4, budget_str, h_format)
        worksheet.set_column(5, 5, 20)
        worksheet.write(row_num, 5, '전월 인출 금액 누계', h_format)
        worksheet.set_column(6, 6, 20)
        worksheet.write(row_num, 6, '당월 인출 금액', h_format)
        worksheet.set_column(7, 7, 20)
        worksheet.write(row_num, 7, '인출 금액 합계', h_format)
        worksheet.set_column(8, 8, 20)
        worksheet.write(row_num, 8, '가용 예산 합계', h_format)

        # 4. Contents (ledger 기반: account가 있고, depth=2, is_category_only=False인 예산만)
        budgets = ProjectOutBudget.objects.filter(
            project=project,
            account__isnull=False,
            account__depth=2,
            account__category='expense',
            account__is_category_only=False
        ).select_related('account', 'account__parent').order_by('order', 'id')

        budget_sum = budgets.aggregate(Sum('budget'))['budget__sum']
        revised_budget_sum = budgets.aggregate(
            revised_budget_sum=Sum(
                Case(
                    When(revised_budget__isnull=True, then=F('budget')),
                    When(revised_budget=0, then=F('budget')),
                    default=F('revised_budget'),
                    output_field=PositiveBigIntegerField()
                )
            )
        )['revised_budget_sum']

        calc_budget_sum = revised_budget_sum if is_revised else budget_sum

        budget_month_sum = 0
        budget_total_sum = 0

        # 중분류별 하위 예산 개수 계산 (ledger 기반: account.parent별 그룹)
        parent_budget_counts = {}
        for budget in budgets:
            parent_pk = budget.account.parent_id if budget.account and budget.account.parent else None
            if parent_pk:
                parent_budget_counts[parent_pk] = parent_budget_counts.get(parent_pk, 0) + 1

        # 중분류별 첫 번째 예산 여부 추적
        parent_first_seen = set()

        # account_opt별 첫 번째 예산 추적
        opt_first_seen = {}

        # 출금 거래만 조회 (sort_id=2) - Vue API와 동일한 로직
        all_transaction_ids = list(ProjectBankTransaction.objects.filter(
            project_id=project.pk,
            sort_id=2,  # 출금만
            deal_date__lte=date
        ).values_list('transaction_id', flat=True))

        month_first = date[:8] + '01'
        month_transaction_ids = list(ProjectBankTransaction.objects.filter(
            project_id=project.pk,
            sort_id=2,  # 출금만
            deal_date__gte=month_first,
            deal_date__lte=date
        ).values_list('transaction_id', flat=True))

        for row, budget in enumerate(budgets):
            row_num += 1

            # ledger 기반: account_id 사용 (출금 거래만)
            budget_entries = ProjectAccountingEntry.objects.filter(
                account_id=budget.account_id,
                transaction_id__in=all_transaction_ids
            )

            # ledger 기반: 당월 출금 거래만
            co_budget_month = ProjectAccountingEntry.objects.filter(
                account_id=budget.account_id,
                transaction_id__in=month_transaction_ids
            ).aggregate(Sum('amount'))['amount__sum']
            co_budget_month = co_budget_month if co_budget_month else 0
            budget_month_sum += co_budget_month

            calc_budget = budget.revised_budget or budget.budget if is_revised else budget.budget
            co_budget_total = budget_entries.aggregate(Sum('amount'))['amount__sum']
            co_budget_total = co_budget_total if co_budget_total else 0
            budget_total_sum += co_budget_total

            # ledger 기반: account.parent_id 사용
            parent_pk = budget.account.parent_id if budget.account and budget.account.parent else None
            opt_budgets = self.get_sub_title(project, budget.account_opt, parent_pk)

            for col in range(9):
                if col == 0 and row == 0:
                    worksheet.merge_range(row_num, col, budgets.count() + 2, col, '사업비', center_format)
                if col == 1:
                    # ledger 기반: account.parent별 병합
                    if parent_pk and parent_pk not in parent_first_seen:
                        parent_first_seen.add(parent_pk)
                        parent_count = parent_budget_counts.get(parent_pk, 1)
                        parent_name = budget.account.parent.name if budget.account.parent else ''
                        worksheet.merge_range(row_num, col,
                                              row_num + parent_count - 1,
                                              col, parent_name, center_format)
                if col == 2:
                    if budget.account_opt:
                        # account_opt별 첫 번째 예산인지 확인
                        opt_key = (parent_pk, budget.account_opt)
                        if opt_key not in opt_first_seen:
                            opt_first_seen[opt_key] = True
                            worksheet.merge_range(row_num, col, row_num + len(opt_budgets) - 1,
                                                  col, budget.account_opt, left_format)
                    else:
                        # ledger 기반: account.name 사용
                        account_name = budget.account.name if budget.account else ''
                        worksheet.merge_range(row_num, col, row_num, col + 1, account_name, left_format)
                if col == 3:
                    if budget.account_opt:
                        # ledger 기반: account.name 사용
                        worksheet.write(row_num, col, budget.account.name if budget.account else '', left_format)
                if col == 4:
                    worksheet.write(row_num, col, calc_budget, number_format)
                if col == 5:
                    worksheet.write(row_num, col, co_budget_total - co_budget_month, number_format)
                if col == 6:
                    worksheet.write(row_num, col, co_budget_month, number_format)
                if col == 7:
                    worksheet.write(row_num, col, co_budget_total, number_format)
                if col == 8:
                    worksheet.write(row_num, col, calc_budget - co_budget_total, number_format)

        # 5. Sum row - Excel SUM 공식 사용 (실제 셀 값 합계)
        row_num += 1
        sum_format = self.create_sum_format(workbook)

        # 데이터 시작 행: 4 (헤더가 3행)
        data_start_row = 4
        data_end_row = row_num  # 현재 row_num은 마지막 데이터 행 + 1이므로, 마지막 데이터 행은 row_num

        worksheet.merge_range(row_num, 0, row_num, 3, '합 계', sum_format)
        # Column E (4): 예산
        worksheet.write_formula(row_num, 4, f'=SUM(E{data_start_row}:E{data_end_row})', sum_format)
        # Column F (5): 전월 인출 금액 누계
        worksheet.write_formula(row_num, 5, f'=SUM(F{data_start_row}:F{data_end_row})', sum_format)
        # Column G (6): 당월 인출 금액
        worksheet.write_formula(row_num, 6, f'=SUM(G{data_start_row}:G{data_end_row})', sum_format)
        # Column H (7): 인출 금액 합계
        worksheet.write_formula(row_num, 7, f'=SUM(H{data_start_row}:H{data_end_row})', sum_format)
        # Column I (8): 가용 예산 합계
        worksheet.write_formula(row_num, 8, f'=SUM(I{data_start_row}:I{data_end_row})', sum_format)

        # data end ----------------------------------------------- #

        # Close the workbook before sending the data.
        filename = request.GET.get('filename')
        filename = f'{filename}-{date}' if filename else f'budget_status-{date}'
        return ExcelExportMixin.create_response(output, workbook, filename)

    @staticmethod
    def get_sub_title(project, sub, parent_pk):
        """ledger 기반: account.parent_id 사용"""
        return ProjectOutBudget.objects.filter(
            project=project,
            account_opt=sub,
            account__parent_id=parent_pk
        ).order_by('account').values_list()


class ExportLedgerCashFlowForm(ExcelExportMixin):
    """프로젝트 자금집행 내역 반영 캐시 플로우 폼"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('캐시_플로우_폼')

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)
        number_format = self.create_number_format(workbook)
        center_format = self.create_center_format(workbook)
        left_format = self.create_left_format(workbook)
        sum_format = self.create_sum_format(workbook)

        # data start --------------------------------------------- #
        project = Project.objects.get(pk=request.GET.get('project'))
        date = request.GET.get('date') or TODAY
        revised = request.GET.get('revised')
        is_revised = int(revised) if revised in ('0', '1') else 0

        # 프로젝트 일정 가져오기 (필수 필드)
        monthly_aggr_start = project.monthly_aggr_start_date
        construction_start = project.construction_start_date
        construction_months = project.construction_period_months
        buffer_months = 5  # 상수

        # 1. 동적 기간 계산
        # 누계 종료일: 월별집계시작일 이전월 마지막 날
        # 월별집계시작일이 2024-02-01이면 누계는 2024-01-31까지
        cumulative_end_date = monthly_aggr_start - relativedelta(days=1)

        # 월별 시작: 월별집계시작일부터
        monthly_start_date = monthly_aggr_start

        monthly_start_year = monthly_start_date.year
        monthly_start_month = monthly_start_date.month

        # 월별 종료: 착공월 + 공사기간 + 여유기간(5개월)
        end_date = construction_start + relativedelta(months=construction_months + buffer_months)
        monthly_end_year = end_date.year
        monthly_end_month = end_date.month

        # 월 목록 생성
        months = []
        current_year, current_month = monthly_start_year, monthly_start_month
        while (current_year, current_month) <= (monthly_end_year, monthly_end_month):
            months.append((current_year, current_month))
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1

        # 2. Title
        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.write(row_num, 0, str(project) + ' 월별 자금집행 현황', title_format)
        row_num += 1

        # 3. Header - 기준일자
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(months) + 6, date + ' 현재', workbook.add_format({'align': 'right'}))
        row_num += 1

        # 4. Column Headers
        # 기본 컬럼 설정
        worksheet.set_column(0, 0, 10)
        worksheet.write(row_num, 0, '대분류', h_format)
        worksheet.set_column(1, 1, 12)
        worksheet.write(row_num, 1, '중분류', h_format)
        worksheet.set_column(2, 2, 18)
        worksheet.write(row_num, 2, '소분류', h_format)
        worksheet.set_column(3, 3, 15)
        budget_str = '현황 예산' if is_revised else '기초 예산'
        worksheet.write(row_num, 3, budget_str, h_format)

        # 누계 컬럼 (동적 헤더)
        worksheet.set_column(4, 4, 15)
        cumulative_label = f"{cumulative_end_date.strftime('%Y-%m-%d')} 이전 누계"
        worksheet.write(row_num, 4, cumulative_label, h_format)

        # 월별 컬럼 헤더
        for idx, (year, month) in enumerate(months):
            col = 5 + idx
            worksheet.set_column(col, col, 12)
            worksheet.write(row_num, col, f'{year}-{month:02d}', h_format)

        # 합계 및 미집행 컬럼 (월별 컬럼 이후)
        total_col = 5 + len(months)
        remaining_col = total_col + 1
        worksheet.set_column(total_col, total_col, 15)
        worksheet.write(row_num, total_col, '집행금액 합계', h_format)
        worksheet.set_column(remaining_col, remaining_col, 15)
        worksheet.write(row_num, remaining_col, '미집행금액', h_format)

        # 5. Fetch budget items (ledger 기반: account가 있고, depth=2, is_category_only=False인 예산만)
        budgets = ProjectOutBudget.objects.filter(
            project=project,
            account__isnull=False,
            account__depth=2,
            account__category='expense',
            account__is_category_only=False
        ).select_related('account', 'account__parent').order_by('order', 'id')

        # 6. Pre-fetch all transactions for optimization
        # 월별집계시작일 이전 누계 (동적) - 출금 거래만 (sort_id=2) - Vue API와 동일한 로직
        cumulative_transaction_ids = ProjectBankTransaction.objects.filter(
            project_id=project.pk,
            sort_id=2,  # 출금만
            deal_date__lte=cumulative_end_date
        ).values_list('transaction_id', flat=True)

        cumulative_data = ProjectAccountingEntry.objects.filter(
            transaction_id__in=cumulative_transaction_ids
        ).values('account_id').annotate(total=Sum('amount'))

        cumulative_dict = {item['account_id']: item['total'] or 0 for item in cumulative_data}

        # 월별 데이터 (월별집계시작일 ~ 종료일) (동적) - 출금 거래만 (sort_id=2)
        monthly_end_date_obj = datetime.date(monthly_end_year, monthly_end_month, 28)
        monthly_transaction_ids = ProjectBankTransaction.objects.filter(
            project_id=project.pk,
            sort_id=2,  # 출금만
            deal_date__gte=monthly_start_date,
            deal_date__lte=monthly_end_date_obj
        ).values_list('transaction_id', flat=True)

        # 월별 거래에서 날짜 정보를 얻기 위해 Join
        bank_transactions_with_dates = ProjectBankTransaction.objects.filter(
            transaction_id__in=monthly_transaction_ids
        ).values('transaction_id', 'deal_date')

        # transaction_id별 날짜 매핑
        transaction_date_map = {t['transaction_id']: t['deal_date'] for t in bank_transactions_with_dates}

        # accounting entry와 날짜 조합
        monthly_accounting_entries = ProjectAccountingEntry.objects.filter(
            transaction_id__in=monthly_transaction_ids
        ).values('account_id', 'transaction_id', 'amount')

        monthly_transactions = []
        for entry in monthly_accounting_entries:
            deal_date = transaction_date_map.get(entry['transaction_id'])
            if deal_date:
                monthly_transactions.append({
                    'account_id': entry['account_id'],
                    'year': deal_date.year,
                    'month': deal_date.month,
                    'amount': entry['amount'] or 0
                })

        # 집계
        from collections import defaultdict
        monthly_aggregated = defaultdict(lambda: defaultdict(int))
        for item in monthly_transactions:
            key = (item['account_id'], item['year'], item['month'])
            monthly_aggregated[key[0]][(key[1], key[2])] += item['amount']

        monthly_dict = {}
        for account_id, date_amounts in monthly_aggregated.items():
            for (year, month), amount in date_amounts.items():
                key = (account_id, year, month)
                monthly_dict[key] = amount

        # 합계 계산을 위한 변수
        total_budget = 0
        total_cumulative = 0
        total_monthly = [0] * len(months)

        # 중분류별 하위 예산 개수 계산 (ledger 기반: account.parent별 그룹)
        parent_budget_counts = {}
        for budget in budgets:
            parent_pk = budget.account.parent_id if budget.account and budget.account.parent else None
            if parent_pk:
                parent_budget_counts[parent_pk] = parent_budget_counts.get(parent_pk, 0) + 1

        # 중분류별 첫 번째 예산 여부 추적
        parent_first_seen = set()

        for row_idx, budget in enumerate(budgets):
            row_num += 1

            # 예산액
            calc_budget = budget.revised_budget or budget.budget if is_revised else budget.budget
            total_budget += calc_budget if calc_budget else 0

            # 누계 (월별집계시작일 이전) - ledger 기반: account_id 사용
            cumulative_amount = cumulative_dict.get(budget.account_id, 0)
            total_cumulative += cumulative_amount

            # 월별 금액 - ledger 기반: account_id 사용
            monthly_amounts = []
            for year, month in months:
                amount = monthly_dict.get((budget.account_id, year, month), 0)
                monthly_amounts.append(amount)

            for idx, amount in enumerate(monthly_amounts):
                total_monthly[idx] += amount

            # 대분류 (첫 행에만 병합)
            if row_idx == 0:
                worksheet.merge_range(row_num, 0, row_num + budgets.count() - 1, 0, '사업비', center_format)

            # 중분류 (account.parent별 병합) - ledger 기반
            parent_pk = budget.account.parent_id if budget.account and budget.account.parent else None
            if parent_pk and parent_pk not in parent_first_seen:
                parent_first_seen.add(parent_pk)
                parent_count = parent_budget_counts.get(parent_pk, 1)
                parent_name = budget.account.parent.name if budget.account.parent else ''
                worksheet.merge_range(row_num, 1,
                                      row_num + parent_count - 1,
                                      1, parent_name, center_format)

            # 소분류 (account) - ledger 기반
            worksheet.write(row_num, 2, budget.account.name if budget.account else '', left_format)

            # 예산액
            worksheet.write(row_num, 3, calc_budget, number_format)

            # 누계
            worksheet.write(row_num, 4, cumulative_amount, number_format)

            # 월별 금액
            for idx, amount in enumerate(monthly_amounts):
                worksheet.write(row_num, 5 + idx, amount, number_format)

            # 집행금액 합계 (수식: 누계 + 월별 합계)
            total_col = 5 + len(months)
            # E열(누계)부터 마지막 월별 컬럼까지 합계
            first_col = 'E'
            last_col = self.get_excel_column(total_col - 1)
            worksheet.write_formula(row_num, total_col, f'=SUM({first_col}{row_num + 1}:{last_col}{row_num + 1})',
                                    number_format)

            # 미집행금액 (수식: 예산 - 집행금액 합계)
            remaining_col = total_col + 1
            budget_col = 'D'
            total_col_letter = self.get_excel_column(total_col)
            worksheet.write_formula(row_num, remaining_col,
                                    f'={budget_col}{row_num + 1}-{total_col_letter}{row_num + 1}', number_format)

        # 8. Sum row
        row_num += 1

        worksheet.merge_range(row_num, 0, row_num, 2, '합 계', sum_format)
        worksheet.write(row_num, 3, total_budget, sum_format)
        worksheet.write(row_num, 4, total_cumulative, sum_format)

        for idx, total in enumerate(total_monthly):
            worksheet.write(row_num, 5 + idx, total, sum_format)

        # 합계 행의 집행금액 합계 및 미집행금액
        total_col = 5 + len(months)
        remaining_col = total_col + 1
        first_col = 'E'
        last_col = self.get_excel_column(total_col - 1)
        worksheet.write_formula(row_num, total_col,
                                f'=SUM({first_col}{row_num + 1}:{last_col}{row_num + 1})',
                                sum_format)

        budget_col = 'D'
        total_col_letter = self.get_excel_column(total_col)
        worksheet.write_formula(row_num, remaining_col,
                                f'={budget_col}{row_num + 1}-{total_col_letter}{row_num + 1}',
                                sum_format)

        # data end ----------------------------------------------- #

        # Close the workbook before sending the data.
        filename = request.GET.get('filename')
        filename = f'{filename}-{date}' if filename else f'{str(project)}-cash-flow-form-{date}'
        return ExcelExportMixin.create_response(output, workbook, filename)

    @staticmethod
    def get_excel_column(col_num):
        """Convert zero-indexed column number to Excel column letter (0 -> A, 25 -> Z, 26 -> AA, etc.)"""
        result = ""
        while col_num >= 0:
            result = chr(col_num % 26 + 65) + result
            col_num = col_num // 26 - 1
        return result

    @staticmethod
    def get_sub_title(project, sub, parent_pk):
        """ledger 기반: account.parent_id 사용"""
        return ProjectOutBudget.objects.filter(
            project=project,
            account_opt=sub,
            account__parent_id=parent_pk
        ).order_by('account').values_list()


def export_pro_transaction_xls(request):
    """프로젝트별 입출금 내역 (공용 서비스 함수 사용)"""
    # 서비스 함수를 직접 호출하므로 ViewSet 관련 import는 더 이상 필요 없음

    filename = request.GET.get('filename')
    filename = f'{filename}-{TODAY}' if filename else f'pro_transaction-{TODAY}'
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}.xls'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('프로젝트_입출금_내역')

    # --- 데이터 조회 로직 (공용 서비스 함수 직접 호출) ---
    # request.GET을 직접 전달하여 모든 필터 파라미터를 서비스 함수가 처리하도록 함
    obj_list = get_project_transactions(request.GET)
    obj_list = obj_list.order_by('deal_date', 'created_at')
    # -----------------------------------------

    # --- N+1 문제 해결을 위한 수동 Prefetch ---
    transaction_ids = [t.transaction_id for t in obj_list]
    if transaction_ids:
        accounting_entries = ProjectAccountingEntry.objects.filter(
            transaction_id__in=transaction_ids
        ).select_related('account')

        entries_map = defaultdict(list)
        for entry in accounting_entries:
            entries_map[entry.transaction_id].append(entry)

        for transaction in obj_list:
            transaction.prefetched_entries = entries_map.get(transaction.transaction_id, [])
    # ------------------------------------

    project = Project.objects.get(pk=request.GET.get('project'))
    pro_name = project.name

    # Sheet Title, first row
    row_num = 0

    style = xlwt.XFStyle()
    style.font.bold = True
    style.font.height = 300
    style.alignment.vert = style.alignment.VERT_CENTER

    ws.write(row_num, 0, pro_name + ' 입출금 내역', style)
    ws.row(0).height_mismatch = True
    ws.row(0).height = 38 * 20

    # Column definitions
    columns = [
        '일시', '메모', '계좌', '적요', '입금액', '출금액',
        '계정', '거래처', '분류금액', '증빙'
    ]

    # Column width settings
    ws.col(0).width = 110 * 30
    ws.col(1).width = 100 * 30
    ws.col(2).width = 170 * 30
    ws.col(3).width = 180 * 30
    ws.col(4).width = 110 * 30
    ws.col(5).width = 110 * 30
    ws.col(6).width = 160 * 30
    ws.col(7).width = 120 * 30
    ws.col(8).width = 110 * 30
    ws.col(9).width = 100 * 30

    # Sheet header, second row
    row_num = 1

    header_style = xlwt.XFStyle()
    header_style.font.bold = True
    header_style.borders.left = 1
    header_style.borders.right = 1
    header_style.borders.top = 1
    header_style.borders.bottom = 1
    header_style.pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    header_style.pattern.pattern_fore_colour = xlwt.Style.colour_map['silver_ega']
    header_style.alignment.vert = header_style.alignment.VERT_CENTER
    header_style.alignment.horz = header_style.alignment.HORZ_CENTER

    for col_num, col_name in enumerate(columns):
        ws.write(row_num, col_num, col_name, header_style)

    # Sheet body, remaining rows
    styles = XlwtStyleMixin.create_xlwt_styles()

    for trans in obj_list:
        entries = getattr(trans, 'prefetched_entries', [])
        if not entries:  # 거래는 있으나 분개가 없는 경우
            row_num += 1
            ws.write(row_num, 0, trans.deal_date.strftime('%Y-%m-%d'), styles['date'])
            ws.write(row_num, 1, trans.note or '', styles['default'])
            ws.write(row_num, 2, trans.bank_account.alias_name if trans.bank_account else '', styles['default'])
            ws.write(row_num, 3, trans.content or '', styles['default'])
            ws.write(row_num, 4, trans.amount if trans.sort.pk == 1 else 0, styles['amount'])
            ws.write(row_num, 5, trans.amount if trans.sort.pk == 2 else 0, styles['amount'])
            for i in range(6, 10):
                ws.write(row_num, i, '', styles['default'])
        elif len(entries) == 1:
            entry = entries[0]
            row_num += 1
            # Bank transaction columns
            ws.write(row_num, 0, trans.deal_date.strftime('%Y-%m-%d'), styles['date'])
            ws.write(row_num, 1, trans.note or '', styles['default'])
            ws.write(row_num, 2, trans.bank_account.alias_name if trans.bank_account else '', styles['default'])
            ws.write(row_num, 3, trans.content or '', styles['default'])
            ws.write(row_num, 4, trans.amount if trans.sort.pk == 1 else 0, styles['amount'])
            ws.write(row_num, 5, trans.amount if trans.sort.pk == 2 else 0, styles['amount'])
            # Classification columns
            ws.write(row_num, 6, entry.account.name if entry.account else '', styles['default'])
            ws.write(row_num, 7, entry.trader or '', styles['default'])
            ws.write(row_num, 8, entry.amount or 0, styles['amount'])
            ws.write(row_num, 9, entry.get_evidence_type_display() or '', styles['default'])
        else:
            for i, acc_entry in enumerate(entries):
                row_num += 1
                if i == 0:
                    # Bank transaction columns - only on the first row
                    ws.write(row_num, 0, trans.deal_date.strftime('%Y-%m-%d'), styles['date'])
                    ws.write(row_num, 1, trans.note or '', styles['default'])
                    ws.write(row_num, 2, trans.bank_account.alias_name if trans.bank_account else '', styles['default'])
                    ws.write(row_num, 3, trans.content or '', styles['default'])
                    ws.write(row_num, 4, trans.amount if trans.sort.pk == 1 else 0, styles['amount'])
                    ws.write(row_num, 5, trans.amount if trans.sort.pk == 2 else 0, styles['amount'])

                # Classification columns are always written
                ws.write(row_num, 6, acc_entry.account.name if acc_entry.account else '', styles['default'])
                ws.write(row_num, 7, acc_entry.trader or '', styles['default'])
                ws.write(row_num, 8, acc_entry.amount or 0, styles['amount'])
                ws.write(row_num, 9, acc_entry.get_evidence_type_display() or '', styles['default'])

    wb.save(response)
    return response
