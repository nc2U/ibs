"""
Cash Excel Export Views

현금 출납 관련 Excel 내보내기 뷰들
"""
import datetime
import io

import xlsxwriter
import xlwt
from dateutil.relativedelta import relativedelta
from django.db.models import Q, Sum, When, F, PositiveBigIntegerField, Case
from django.http import HttpResponse

from _excel.mixins import ExcelExportMixin
from cash.models import CashBook, ProjectCashBook
from company.models import Company
from project.models import Project, ProjectOutBudget

TODAY = datetime.date.today().strftime('%Y-%m-%d')


class ExportProjectBalance(ExcelExportMixin):
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
        qs = ProjectCashBook.objects.filter(
            is_separate=False,
            bank_account__directpay=False,
            deal_date__lte=date
        ).order_by('bank_account')

        return qs.annotate(
            bank_acc=F('bank_account__alias_name'),
            bank_num=F('bank_account__number')
        ).values('bank_acc', 'bank_num').annotate(
            inc_sum=Sum('income'),
            out_sum=Sum('outlay'),
            date_inc=Sum(Case(When(deal_date=date, then=F('income')), default=0)),
            date_out=Sum(Case(When(deal_date=date, then=F('outlay')), default=0))
        )


class ExportProjectDateCashbook(ExcelExportMixin):
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

        # 3. Header
        worksheet.set_column(0, 0, 15)
        worksheet.write(row_num, 0, '항목', h_format)
        worksheet.set_column(1, 1, 15)
        worksheet.write(row_num, 1, '세부항목', h_format)
        worksheet.set_column(2, 2, 20)
        worksheet.write(row_num, 2, '입금 금액', h_format)
        worksheet.set_column(3, 3, 20)
        worksheet.write(row_num, 3, '출금 금액', h_format)
        worksheet.set_column(4, 4, 25)
        worksheet.write(row_num, 4, '거래 계좌', h_format)
        worksheet.set_column(5, 5, 30)
        worksheet.write(row_num, 5, '거래처', h_format)
        worksheet.set_column(6, 6, 30)
        worksheet.write(row_num, 6, '적요', h_format)

        # 4. Contents
        date_cashes = ProjectCashBook.objects.filter(is_separate=False, deal_date__exact=date).order_by(
            'deal_date', 'created', 'id')

        inc_sum = 0
        out_sum = 0
        for row, cash in enumerate(date_cashes):
            row_num += 1
            inc_sum += cash.income if cash.income else 0
            out_sum += cash.outlay if cash.outlay else 0

            for col in range(7):
                if col == 0:
                    worksheet.write(row_num, col, cash.project_account_d2.name, center_format)
                if col == 1:
                    worksheet.write(row_num, col, cash.project_account_d3.name, center_format)
                if col == 2:
                    worksheet.write(row_num, col, cash.income, number_format)
                if col == 3:
                    worksheet.write(row_num, col, cash.outlay, number_format)
                if col == 4:
                    worksheet.write(row_num, col, cash.bank_account.alias_name, left_format)
                if col == 5:
                    worksheet.write(row_num, col, cash.trader, left_format)
                if col == 6:
                    worksheet.write(row_num, col, cash.content, left_format)

        # 5. Sum row
        row_num += 1
        h_format.set_num_format(41)
        worksheet.merge_range(row_num, 0, row_num, 1, '합계', h_format)
        worksheet.write(row_num, 2, inc_sum, h_format)
        worksheet.write(row_num, 3, out_sum, h_format)
        worksheet.write(row_num, 4, '', h_format)
        worksheet.write(row_num, 5, '', h_format)
        worksheet.write(row_num, 6, '', h_format)

        # data end ----------------------------------------------- #

        # Close the workbook before sending the data.
        filename = request.GET.get('filename')
        filename = f'{filename}-{date}' if filename else f'project-date-cashbook-{date}'
        return ExcelExportMixin.create_response(output, workbook, filename)


class ExportBudgetExecutionStatus(ExcelExportMixin):
    """프로젝트 예산 대비 현황"""

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

        # 4. Contents
        budgets = ProjectOutBudget.objects.filter(project=project)
        budget_sum = budgets.aggregate(Sum('budget'))['budget__sum']
        revised_budget_sum = budgets.aggregate(
            revised_budget_sum=Sum(
                Case(
                    When(revised_budget__isnull=True, then=F('budget')),
                    When(revised_budget=0, then=F('budget')),
                    default=F('revised_budget'),
                    output_field=PositiveBigIntegerField()  # budget 및 revised_budget의 필드 타입에 맞게 조정
                )
            )
        )['revised_budget_sum']

        calc_budget_sum = revised_budget_sum if is_revised else budget_sum

        budget_month_sum = 0
        budget_total_sum = 0

        for row, budget in enumerate(budgets):
            row_num += 1
            co_budget = ProjectCashBook.objects.filter(project=project,
                                                       project_account_d3=budget.account_d3,
                                                       deal_date__lte=date)

            co_budget_month = co_budget.filter(deal_date__gte=date[:8] + '01').aggregate(Sum('outlay'))['outlay__sum']
            co_budget_month = co_budget_month if co_budget_month else 0
            budget_month_sum += co_budget_month

            calc_budget = budget.revised_budget or budget.budget if is_revised else budget.budget
            co_budget_total = co_budget.aggregate(Sum('outlay'))['outlay__sum']
            co_budget_total = co_budget_total if co_budget_total else 0
            budget_total_sum += co_budget_total

            opt_budgets = self.get_sub_title(project, budget.account_opt, budget.account_d2.pk)

            for col in range(9):
                if col == 0 and row == 0:
                    worksheet.merge_range(row_num, col, budgets.count() + 2, col, '사업비', center_format)
                if col == 1:
                    if int(budget.account_d3.code) == int(budget.account_d2.code) + 1:
                        worksheet.merge_range(row_num, col,
                                              row_num + budget.account_d2.projectoutbudget_set.count() - 1,
                                              col, budget.account_d2.name, center_format)
                if col == 2:
                    if budget.account_opt:
                        if budget.account_d3.pk == opt_budgets[0][4]:
                            worksheet.merge_range(row_num, col, row_num + len(opt_budgets) - 1,
                                                  col, budget.account_opt, left_format)
                    else:
                        worksheet.merge_range(row_num, col, row_num, col + 1, budget.account_d3.name, left_format)
                if col == 3:
                    if budget.account_opt:
                        worksheet.write(row_num, col, budget.account_d3.name, left_format)
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

        # 5. Sum row
        row_num += 1
        worksheet.merge_range(row_num, 0, row_num, 3, '합 계', center_format)
        worksheet.write(row_num, 4, calc_budget_sum, number_format)
        worksheet.write(row_num, 5, budget_total_sum - budget_month_sum, number_format)
        worksheet.write(row_num, 6, budget_month_sum, number_format)
        worksheet.write(row_num, 7, budget_total_sum, number_format)
        worksheet.write(row_num, 8, calc_budget_sum - budget_total_sum, number_format)

        # data end ----------------------------------------------- #

        # Close the workbook before sending the data.
        filename = request.GET.get('filename')
        filename = f'{filename}-{date}' if filename else f'budget_status-{date}'
        return ExcelExportMixin.create_response(output, workbook, filename)

    @staticmethod
    def get_sub_title(project, sub, d2):
        return ProjectOutBudget.objects.filter(project=project,
                                               account_opt=sub,
                                               account_d2__id=d2).order_by('account_d3').values_list()


class ExportCashFlowForm(ExcelExportMixin):
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

        # 5. Fetch budget items
        budgets = ProjectOutBudget.objects.filter(project=project).order_by('order', 'id')

        # 6. Pre-fetch all transactions for optimization
        # 월별집계시작일 이전 누계 (동적)
        cumulative_data = ProjectCashBook.objects.filter(
            project=project,
            is_separate=False,
            deal_date__lte=cumulative_end_date
        ).values('project_account_d3_id').annotate(total=Sum('outlay'))

        cumulative_dict = {item['project_account_d3_id']: item['total'] or 0 for item in cumulative_data}

        # 월별 데이터 (월별집계시작일 ~ 종료일) (동적)
        monthly_end_date_obj = datetime.date(monthly_end_year, monthly_end_month, 28)
        monthly_transactions = ProjectCashBook.objects.filter(
            project=project,
            is_separate=False,
            deal_date__gte=monthly_start_date,
            deal_date__lte=monthly_end_date_obj
        ).annotate(
            year=F('deal_date__year'),
            month=F('deal_date__month')
        ).values('project_account_d3_id', 'year', 'month').annotate(total=Sum('outlay'))

        monthly_dict = {}
        for item in monthly_transactions:
            key = (item['project_account_d3_id'], item['year'], item['month'])
            monthly_dict[key] = item['total'] or 0

        # 합계 계산을 위한 변수
        total_budget = 0
        total_cumulative = 0
        total_monthly = [0] * len(months)

        for row_idx, budget in enumerate(budgets):
            row_num += 1

            # 예산액
            calc_budget = budget.revised_budget or budget.budget if is_revised else budget.budget
            total_budget += calc_budget if calc_budget else 0

            # 누계 (월별집계시작일 이전)
            cumulative_amount = cumulative_dict.get(budget.account_d3_id, 0)
            total_cumulative += cumulative_amount

            # 월별 금액
            monthly_amounts = []
            for year, month in months:
                amount = monthly_dict.get((budget.account_d3_id, year, month), 0)
                monthly_amounts.append(amount)

            for idx, amount in enumerate(monthly_amounts):
                total_monthly[idx] += amount

            # 대분류 (첫 행에만 병합)
            if row_idx == 0:
                worksheet.merge_range(row_num, 0, row_num + budgets.count() - 1, 0, '사업비', center_format)

            # 중분류 (account_d2별 병합)
            if int(budget.account_d3.code) == int(budget.account_d2.code) + 1:
                worksheet.merge_range(row_num, 1,
                                      row_num + budget.account_d2.projectoutbudget_set.count() - 1,
                                      1, budget.account_d2.name, center_format)

            # 소분류 (account_d3)
            worksheet.write(row_num, 2, budget.account_d3.name, left_format)

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
    def get_sub_title(project, sub, d2):
        return ProjectOutBudget.objects.filter(project=project, account_opt=sub, account_d2__id=d2).order_by(
            'account_d3').values_list()


def export_project_cash_xls(request):
    """프로젝트별 입출금 내역"""
    sdate = request.GET.get('sdate')
    edate = request.GET.get('edate')

    sdate = '1900-01-01' if not sdate or sdate == 'null' else sdate
    edate = TODAY if not edate or edate == 'null' else edate

    is_imp = request.GET.get('imp')
    frontname = request.GET.get('filename')
    filename = 'imprest' if is_imp == '1' else 'cashbook'
    filename = f'filename={edate}-project-{filename}'
    filename = f'{frontname}-{edate}' if filename else f'{filename}-{edate}'

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}.xls'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('프로젝트_입출금_내역')  # 시트 이름

    # get_data: ?project=1&sdate=2020-12-01&edate=2020-12-31&sort=1&d1=1&d2=1&bank_acc=5&q=ㅁ
    project = Project.objects.get(pk=request.GET.get('project'))
    sort = request.GET.get('sort')
    d1 = request.GET.get('d1')
    d2 = request.GET.get('d2')
    bank_acc = request.GET.get('bank_acc')
    q = request.GET.get('q')

    cash_list = ProjectCashBook.objects.filter(project=project,
                                               is_separate=False,
                                               deal_date__range=(sdate, edate)) \
        .order_by('deal_date', 'created')

    imp_list = ProjectCashBook.objects.filter(project=project, is_imprest=True, is_separate=False,
                                              deal_date__range=(sdate, edate)).exclude(project_account_d3=63,
                                                                                       income__isnull=True)
    obj_list = imp_list if is_imp == '1' else cash_list
    obj_list = obj_list.filter(sort_id=sort) if sort else obj_list
    obj_list = obj_list.filter(project_account_d2_id=d1) if d1 else obj_list
    obj_list = obj_list.filter(project_account_d3_id=d2) if d2 else obj_list
    obj_list = obj_list.filter(bank_account_id=bank_acc) if bank_acc else obj_list
    obj_list = obj_list.filter(
        Q(contract__contractor__name__icontains=q) |
        Q(content__icontains=q) |
        Q(trader__icontains=q) |
        Q(note__icontains=q)) if q else obj_list

    # Sheet Title, first row
    row_num = 0

    style = xlwt.XFStyle()
    style.font.bold = True
    style.font.height = 300
    style.alignment.vert = style.alignment.VERT_CENTER  # 수직정렬

    ws.write(row_num, 0, str(project) + ' 입출금 내역', style)
    ws.row(0).height_mismatch = True
    ws.row(0).height = 38 * 20

    # title_list

    resources = [
        ['거래일자', 'deal_date'],
        ['구분', 'sort__name'],
        ['현장 계정', 'project_account_d2__name'],
        ['현장 세부계정', 'project_account_d3__name'],
        ['적요', 'content'],
        ['거래처', 'trader'],
        ['거래 계좌', 'bank_account__alias_name'],
        ['입금 금액', 'income'],
        ['출금 금액', 'outlay'],
        ['비고', 'note']]

    columns = []
    params = []

    for rsc in resources:
        columns.append(rsc[0])
        params.append(rsc[1])

    rows = obj_list.values_list(*params)

    # Sheet header, second row
    row_num = 1

    style = xlwt.XFStyle()
    style.font.bold = True

    # 테두리 설정
    # 가는 실선 : 1, 작은 굵은 실선 : 2,가는 파선 : 3, 중간가는 파선 : 4, 큰 굵은 실선 : 5, 이중선 : 6,가는 점선 : 7
    # 큰 굵은 점선 : 8,가는 점선 : 9, 굵은 점선 : 10,가는 이중 점선 : 11, 굵은 이중 점선 : 12, 사선 점선 : 13
    style.borders.left = 1
    style.borders.right = 1
    style.borders.top = 1
    style.borders.bottom = 1

    style.pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    style.pattern.pattern_fore_colour = xlwt.Style.colour_map['silver_ega']

    style.alignment.vert = style.alignment.VERT_CENTER  # 수직정렬
    style.alignment.horz = style.alignment.HORZ_CENTER  # 수평정렬

    for col_num, col in enumerate(columns):
        ws.write(row_num, col_num, col, style)

    # Sheet body, remaining rows
    style = xlwt.XFStyle()
    # 테두리 설정
    style.borders.left = 1
    style.borders.right = 1
    style.borders.top = 1
    style.borders.bottom = 1

    style.alignment.vert = style.alignment.VERT_CENTER  # 수직정렬
    # style.alignment.horz = style.alignment.HORZ_CENTER  # 수평정렬

    for row in rows:
        row_num += 1
        for col_num, col in enumerate(columns):
            row = list(row)

            if col == '거래일자':
                style.num_format_str = 'yyyy-mm-dd'
                ws.col(col_num).width = 110 * 30
            if col == '구분':
                if row[col_num] == '1':
                    row[col_num] = '입금'
                if row[col_num] == '2':
                    row[col_num] = '출금'
                if row[col_num] == '3':
                    row[col_num] = '대체'
            if col == '현장 계정':
                ws.col(col_num).width = 110 * 30
            if col == '현장 세부계정':
                ws.col(col_num).width = 160 * 30
            if col == '적요' or col == '거래처':
                ws.col(col_num).width = 180 * 30
            if col == '거래 계좌':
                ws.col(col_num).width = 170 * 30
            if '금액' in col:
                style.num_format_str = '#,##'
                ws.col(col_num).width = 110 * 30
            if col == '비고':
                ws.col(col_num).width = 256 * 30

            ws.write(row_num, col_num, row[col_num], style)

    wb.save(response)
    return response


class ExportBalanceByAcc(ExcelExportMixin):
    """본사 계좌별 잔고 내역"""

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
        worksheet.write(row_num, 4, '금알입금(증가)', h_format)
        worksheet.set_column(5, 5, 20)
        worksheet.write(row_num, 5, '금일출금(감소)', h_format)
        worksheet.set_column(6, 6, 20)
        worksheet.write(row_num, 6, '금일잔고', h_format)

        # 4. Contents
        qs = CashBook.objects.filter(company=company) \
            .order_by('bank_account') \
            .filter(is_separate=False, deal_date__lte=date)

        balance_set = qs.annotate(bank_acc=F('bank_account__alias_name'),
                                  bank_num=F('bank_account__number')) \
            .values('bank_acc', 'bank_num') \
            .annotate(inc_sum=Sum('income'),
                      out_sum=Sum('outlay'),
                      date_inc=Sum(Case(
                          When(deal_date=date, then=F('income')),
                          default=0
                      )),
                      date_out=Sum(Case(
                          When(deal_date=date, then=F('outlay')),
                          default=0
                      )))

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


class ExportDateCashbook(ExcelExportMixin):
    """본사 일별 입출금 내역"""

    @staticmethod
    def get(request):
        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Even though the final file will be in memory, the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example, the Google App Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('당일_입출금내역')

        worksheet.set_default_row(20)  # 기본 행 높이

        # data start --------------------------------------------- #

        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')
        date = request.GET.get('date')
        date = TODAY if not date or date == 'null' else date

        # 1. Title
        row_num = 0
        title_format = workbook.add_format()
        worksheet.set_row(row_num, 50)
        title_format.set_font_size(18)
        title_format.set_align('vcenter')
        title_format.set_bold()
        worksheet.write(row_num, 0, com_name + ' 당일 입출금내역 [' + date + ' 기준]', title_format)

        # 2. Header
        row_num = 1
        worksheet.set_row(row_num, 18)
        # worksheet.write(row_num, 7, date + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header
        row_num = 2
        h_format = workbook.add_format()
        h_format.set_bold()
        h_format.set_border()
        h_format.set_align('center')
        h_format.set_align('vcenter')
        h_format.set_bg_color('#eeeeee')

        worksheet.set_column(0, 0, 15)
        worksheet.write(row_num, 0, '구분', h_format)
        worksheet.set_column(1, 1, 15)
        worksheet.write(row_num, 1, '항목', h_format)
        worksheet.set_column(2, 2, 15)
        worksheet.write(row_num, 2, '세부항목', h_format)
        worksheet.set_column(3, 3, 20)
        worksheet.write(row_num, 3, '입금 금액', h_format)
        worksheet.set_column(4, 4, 20)
        worksheet.write(row_num, 4, '출금 금액', h_format)
        worksheet.set_column(5, 5, 25)
        worksheet.write(row_num, 5, '거래 계좌', h_format)
        worksheet.set_column(6, 6, 30)
        worksheet.write(row_num, 6, '거래처', h_format)
        worksheet.set_column(7, 7, 30)
        worksheet.write(row_num, 7, '적요', h_format)

        # 4. Contents
        b_format = workbook.add_format()
        b_format.set_valign('vcenter')
        b_format.set_border()
        b_format.set_num_format(41)

        date_cashes = CashBook.objects.filter(company=company, is_separate=False,
                                              deal_date__exact=date).order_by('deal_date', 'created', 'id')

        inc_sum = 0
        out_sum = 0
        for row, cash in enumerate(date_cashes):
            row_num += 1
            inc_sum += cash.income if cash.income else 0
            out_sum += cash.outlay if cash.outlay else 0

            for col in range(8):
                if col == 0:
                    worksheet.write(row_num, col, cash.sort.name + '-' + cash.account_d1.name, b_format)
                if col == 1:
                    worksheet.write(row_num, col, cash.account_d2.name, b_format)
                if col == 2:
                    worksheet.write(row_num, col, cash.account_d3.name, b_format)
                if col == 3:
                    worksheet.write(row_num, col, cash.income, b_format)
                if col == 4:
                    worksheet.write(row_num, col, cash.outlay, b_format)
                if col == 5:
                    worksheet.write(row_num, col, cash.bank_account.alias_name, b_format)
                if col == 6:
                    worksheet.write(row_num, col, cash.trader, b_format)
                if col == 7:
                    worksheet.write(row_num, col, cash.content, b_format)

        # 5. Sum row
        row_num += 1
        h_format.set_num_format(41)
        worksheet.merge_range(row_num, 0, row_num, 1, '합계', h_format)
        worksheet.write(row_num, 2, '', h_format)
        worksheet.write(row_num, 3, inc_sum, h_format)
        worksheet.write(row_num, 4, out_sum, h_format)
        worksheet.write(row_num, 5, '', h_format)
        worksheet.write(row_num, 6, '', h_format)
        worksheet.write(row_num, 7, '', h_format)

        # data end ----------------------------------------------- #

        # Close the workbook before sending the data.
        filename = request.GET.get('filename')
        filename = f'{filename}-{date}' if filename else f'date-cashbook-{date}'
        return ExcelExportMixin.create_response(output, workbook, filename)


def export_cashbook_xls(request):
    """본사 입출금 내역"""
    filename = request.GET.get('filename')
    filename = f'{filename}-{TODAY}' if filename else f'cashbook-{TODAY}'
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}.xls'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('본사_입출금_내역')  # 시트 이름

    # get_data: ?s_date=2018-06-30&e_date=&category1=&category2=&bank_account=&search_word=
    s_date = request.GET.get('s_date')
    e_date = request.GET.get('e_date')
    sort = request.GET.get('sort')
    account_d1 = request.GET.get('account_d1')
    account_d2 = request.GET.get('account_d2')
    account_d3 = request.GET.get('account_d3')
    bank_account = request.GET.get('bank_account')
    search_word = request.GET.get('search_word')

    company = Company.objects.get(pk=request.GET.get('company'))
    com_name = company.name.replace('주식회사 ', '(주)')
    sd = '1900-01-01' if not s_date or s_date == 'null' else s_date
    ed = TODAY if not e_date or e_date == 'null' else e_date

    obj_list = CashBook.objects.filter(company=company, is_separate=False,
                                       deal_date__range=(sd, ed)).order_by('deal_date', 'id')

    obj_list = obj_list.filter(sort_id=sort) if sort else obj_list
    obj_list = obj_list.filter(account_d1_id=account_d1) if account_d1 else obj_list
    obj_list = obj_list.filter(account_d2_id=account_d2) if account_d2 else obj_list
    obj_list = obj_list.filter(account_d3_id=account_d3) if account_d3 else obj_list
    obj_list = obj_list.filter(bank_account_id=bank_account) if bank_account else obj_list
    obj_list = obj_list.filter(
        Q(content__icontains=search_word) |
        Q(trader__icontains=search_word) |
        Q(note__icontains=search_word)) if search_word else obj_list

    # Sheet Title, first row
    row_num = 0

    style = xlwt.XFStyle()
    style.font.bold = True
    style.font.height = 300
    style.alignment.vert = style.alignment.VERT_CENTER  # 수직정렬

    ws.write(row_num, 0, com_name + ' 입출금 내역', style)
    ws.row(0).height_mismatch = True
    ws.row(0).height = 38 * 20

    # title_list

    resources = [
        ['거래일자', 'deal_date'],
        ['구분', 'sort__name'],
        ['계정', 'account_d1__name'],
        ['중분류', 'account_d2__name'],
        ['세부계정', 'account_d3__name'],
        ['적요', 'content'],
        ['거래처', 'trader'],
        ['거래계좌', 'bank_account__alias_name'],
        ['입금금액', 'income'],
        ['출금금액', 'outlay'],
        ['비고', 'note']]

    columns = []
    params = []

    for rsc in resources:
        columns.append(rsc[0])
        params.append(rsc[1])

    rows = obj_list.values_list(*params)

    # Sheet header, second row
    row_num = 1

    style = xlwt.XFStyle()
    style.font.bold = True

    # 테두리 설정
    # 가는 실선 : 1, 작은 굵은 실선 : 2,가는 파선 : 3, 중간가는 파선 : 4, 큰 굵은 실선 : 5, 이중선 : 6,가는 점선 : 7
    # 큰 굵은 점선 : 8,가는 점선 : 9, 굵은 점선 : 10,가는 이중 점선 : 11, 굵은 이중 점선 : 12, 사선 점선 : 13
    style.borders.left = 1
    style.borders.right = 1
    style.borders.top = 1
    style.borders.bottom = 1

    style.pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    style.pattern.pattern_fore_colour = xlwt.Style.colour_map['silver_ega']

    style.alignment.vert = style.alignment.VERT_CENTER  # 수직정렬
    style.alignment.horz = style.alignment.HORZ_CENTER  # 수평정렬

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], style)

    # Sheet body, remaining rows
    style = xlwt.XFStyle()
    # 테두리 설정
    style.borders.left = 1
    style.borders.right = 1
    style.borders.top = 1
    style.borders.bottom = 1

    style.alignment.vert = style.alignment.VERT_CENTER  # 수직정렬
    # style.alignment.horz = style.alignment.HORZ_CENTER  # 수평정렬

    for row in rows:
        row_num += 1
        for col_num, col in enumerate((columns)):
            row = list(row)

            if col == '거래일자':
                style.num_format_str = 'yyyy-mm-dd'
                ws.col(col_num).width = 110 * 30

            if col == '구분':
                if row[col_num] == '1':
                    row[col_num] = '입금'
                if row[col_num] == '2':
                    row[col_num] = '출금'
                if row[col_num] == '3':
                    row[col_num] = '대체'

            if col == '계정':
                if row[col_num] == '1':
                    row[col_num] = '자산'
                if row[col_num] == '2':
                    row[col_num] = '부채'
                if row[col_num] == '3':
                    row[col_num] = '자본'
                if row[col_num] == '4':
                    row[col_num] = '수익'
                if row[col_num] == '5':
                    row[col_num] = '비용'
                if row[col_num] == '6':
                    row[col_num] = '대체'

            if col == '현장 계정':
                ws.col(col_num).width = 110 * 30

            if col == '세부계정':
                ws.col(col_num).width = 160 * 30

            if col == '적요' or col == '거래처':
                ws.col(col_num).width = 180 * 30

            if col == '거래계좌':
                ws.col(col_num).width = 170 * 30

            if '금액' in col:
                style.num_format_str = '#,##'
                ws.col(col_num).width = 110 * 30

            if col == '증빙자료':
                if row[col_num] == '0':
                    row[col_num] = '증빙 없음'
                if row[col_num] == '1':
                    row[col_num] = '세금계산서'
                if row[col_num] == '2':
                    row[col_num] = '계산서(면세)'
                if row[col_num] == '3':
                    row[col_num] = '신용카드전표'
                if row[col_num] == '4':
                    row[col_num] = '현금영수증'
                if row[col_num] == '5':
                    row[col_num] = '간이영수증'
                ws.col(col_num).width = 100 * 30

            if col == '비고':
                ws.col(col_num).width = 256 * 30

            ws.write(row_num, col_num, row[col_num], style)

    wb.save(response)
    return response
