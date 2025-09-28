"""
Cash Excel Export Views

현금 출납 관련 Excel 내보내기 뷰들
"""
import datetime
import xlwt
from django.db.models import Q
from django.http import HttpResponse

from _excel.mixins import ExcelExportMixin, ProjectFilterMixin
from _excel.utils import create_filename
from cash.models import CashBook, ProjectCashBook
from company.models import Company
from project.models import Project

TODAY = datetime.date.today().strftime('%Y-%m-%d')


class ExportBalanceByAcc(ExcelExportMixin, ProjectFilterMixin):
    """계정별 잔액 Excel 내보내기"""

    def get(self, request):
        project = self.get_project(request)

        # Excel 워크북 생성
        output, workbook, worksheet = self.create_workbook('계정별_잔액')

        # 제목 작성
        row_num = self.write_title(worksheet, workbook, 0, 10,
                                   f'{project} 계정별 잔액')

        filename = create_filename('balance_by_account', project.name)
        return self.create_response(output, workbook, filename)


class ExportDateCashbook(ExcelExportMixin, ProjectFilterMixin):
    """일별 출납부 Excel 내보내기"""

    def get(self, request):
        project = self.get_project(request)

        # Excel 워크북 생성
        output, workbook, worksheet = self.create_workbook('일별_출납부')

        # 제목 작성
        row_num = self.write_title(worksheet, workbook, 0, 10,
                                   f'{project} 일별 출납부')

        filename = create_filename('date_cashbook', project.name)
        return self.create_response(output, workbook, filename)


def export_cashbook_xls(request):
    """본사 입출금 내역"""
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename={date}-cashbook.xls'.format(date=TODAY)

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

    company = Company.objects.first()
    today = TODAY
    s_date = s_date if s_date else '1900-01-01'
    e_date = e_date if e_date else today

    obj_list = CashBook.objects.filter(company=company, deal_date__range=(s_date, e_date)).order_by('deal_date', 'id')

    if sort:
        obj_list = obj_list.filter(sort_id=sort)

    if account_d1:
        obj_list = obj_list.filter(account_d1_id=account_d1)

    if account_d2:
        obj_list = obj_list.filter(account_d2_id=account_d2)

    if account_d3:
        obj_list = obj_list.filter(account_d3_id=account_d3)

    if bank_account:
        obj_list = obj_list.filter(bank_account_id=bank_account)

    if search_word:
        obj_list = obj_list.filter(
            Q(content__icontains=search_word) |
            Q(trader__icontains=search_word) |
            Q(note__icontains=search_word))

    # Sheet Title, first row
    row_num = 0

    style = xlwt.XFStyle()
    style.font.bold = True
    style.font.height = 300
    style.alignment.vert = style.alignment.VERT_CENTER  # 수직정렬

    ws.write(row_num, 0, str(company) + ' 입출금 내역', style)
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


class ExportProjectBalance(ExcelExportMixin, ProjectFilterMixin):
    """프로젝트 수지현황 Excel 내보내기"""

    def get(self, request):
        project = self.get_project(request)

        # Excel 워크북 생성
        output, workbook, worksheet = self.create_workbook('프로젝트_수지현황')

        # 제목 작성
        row_num = self.write_title(worksheet, workbook, 0, 10,
                                   f'{project} 프로젝트 수지현황')

        # 기본 구조 (상세 구현은 원본 참조)
        filename = create_filename('project_balance', project.name)
        return self.create_response(output, workbook, filename)


class ExportProjectDateCashbook(ExcelExportMixin, ProjectFilterMixin):
    """프로젝트 일별 출납부 Excel 내보내기"""

    def get(self, request):
        project = self.get_project(request)

        # Excel 워크북 생성
        output, workbook, worksheet = self.create_workbook('프로젝트_일별출납부')

        # 제목 작성
        row_num = self.write_title(worksheet, workbook, 0, 10,
                                   f'{project} 일별 출납부')

        filename = create_filename('project_date_cashbook', project.name)
        return self.create_response(output, workbook, filename)


def export_project_cash_xls(request):
    """프로젝트별 입출금 내역"""
    sdate = request.GET.get('sdate')
    edate = request.GET.get('edate')

    sdate = '1900-01-01' if not sdate or sdate == 'null' else sdate
    edate = TODAY if not edate or edate == 'null' else edate

    is_imp = request.GET.get('imp')
    filename = 'imprest' if is_imp == '1' else 'cashbook'

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={edate}-project-{filename}.xls'

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
