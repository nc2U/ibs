"""
Payment Excel Export Views

납부 관련 Excel 내보내기 뷰들
"""
import datetime
import io

import xlsxwriter
import xlwt
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponse
from django.views.generic import View

from apiV1.views.payment import PaymentStatusByUnitTypeViewSet, OverallSummaryViewSet
from cash.models import ProjectCashBook
from contract.models import Contract
from payment.models import InstallmentPaymentOrder, SalesPriceByGT, DownPayment
from project.models import Project, ProjectIncBudget

TODAY = datetime.date.today().strftime('%Y-%m-%d')


def export_payments_xls(request):
    """수납건별 수납내역 리스트"""
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename={date}-payments.xls'.format(date=TODAY)

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('수납건별_납부내역')  # 시트 이름

    # get_data: ?project=1&sd=2020-12-01&ed=2020-12-02&ipo=4&ba=5&up=on&q=#
    project = Project.objects.get(pk=request.GET.get('project'))
    sd = request.GET.get('sd')
    ed = request.GET.get('ed')
    og = request.GET.get('og')
    ut = request.GET.get('ut')
    ipo = request.GET.get('ipo')
    ba = request.GET.get('ba')
    nc = request.GET.get('nc')
    ni = request.GET.get('ni')
    q = request.GET.get('q')

    sd = sd if sd else '1900-01-01'
    ed = TODAY if not ed or ed == 'null' else ed
    obj_list = ProjectCashBook.objects.filter(project=project,
                                              income__isnull=False,
                                              project_account_d3__is_payment=True,
                                              deal_date__range=(sd, ed)).order_by('deal_date', 'created')

    obj_list = obj_list.filter(contract__order_group=og) if og else obj_list
    obj_list = obj_list.filter(contract__unit_type=ut) if ut else obj_list
    obj_list = obj_list.filter(installment_order_id=ipo) if ipo else obj_list
    obj_list = obj_list.filter(bank_account__id=ba) if ba else obj_list
    obj_list = obj_list.filter(contract__isnull=True) if nc else obj_list
    obj_list = obj_list.filter(installment_order__isnull=True, contract__isnull=False) if ni else obj_list
    obj_list = obj_list = obj_list.filter(
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

    ws.write(row_num, 0, str(project) + ' 계약자 대금 납부내역', style)
    ws.row(0).height_mismatch = True
    ws.row(0).height = 38 * 20

    # title_list

    resources = [
        ['거래일자', 'deal_date'],
        ['차수', 'contract__order_group__name'],
        ['타입', 'contract__key_unit__unit_type__name'],
        ['일련번호', 'contract__serial_number'],
        ['계약자', 'contract__contractor__name'],
        ['입금 금액', 'income'],
        ['납입회차', 'installment_order__pay_name'],
        ['수납계좌', 'bank_account__alias_name'],
        ['입금자', 'trader']
    ]

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
        for col_num, col in enumerate(columns):
            row = list(row)

            if col_num == 0:
                style.num_format_str = 'yyyy-mm-dd'
                ws.col(col_num).width = 110 * 30

            if '금액' in col:
                style.num_format_str = '#,##'
                style.alignment.horz = style.alignment.HORZ_RIGHT
                ws.col(col_num).width = 110 * 30

            if col == '차수' or col == '납입회차' or col == '일련번호':
                ws.col(col_num).width = 110 * 30

            if col == '수납계좌':
                ws.col(col_num).width = 170 * 30

            if col == '입금자' or col == '계약자':
                ws.col(col_num).width = 110 * 30

            ws.write(row_num, col_num, row[col_num], style)

    wb.save(response)
    return response


class ExportPayments(View):
    """수납건별 수납내역 리스트"""

    @staticmethod
    def get(request):

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('수납건별_납부내역')

        worksheet.set_default_row(20)

        project = Project.objects.get(pk=request.GET.get('project'))
        sd = request.GET.get('sd')
        ed = request.GET.get('ed')
        sd = sd if sd else '1900-01-01'
        ed = TODAY if not ed or ed == 'null' else ed

        # title_list
        header_src = [
            ['거래일자', 'deal_date', 12],
            ['차수', 'contract__order_group__name', 12],
            ['타입', 'contract__key_unit__unit_type__name', 10],
            ['일련번호', 'contract__serial_number', 12],
            ['계약자', 'contract__contractor__name', 11],
            ['입금 금액', 'income', 12],
            ['납입회차', 'installment_order__pay_name', 13],
            ['수납계좌', 'bank_account__alias_name', 20],
            ['입금자', 'trader', 20],
            ['공급계약체결일', 'contract__sup_cont_date', 15],
        ]

        if project.is_unit_set:
            header_src.insert(4, ['동', 'contract__key_unit__houseunit__building_unit__name', 7])
            header_src.insert(5, ['호수', 'contract__key_unit__houseunit__name', 7])

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)
        title_format = workbook.add_format()
        title_format.set_bold()
        title_format.set_font_size(18)
        title_format.set_align('vcenter')
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, str(project) + ' 계약자 대금 납부내역', title_format)

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, ed + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header - 1
        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

        titles = []  # header titles
        params = []  # ORM 추출 field
        widths = []  # No. 컬럼 넓이

        for ds in header_src:
            if ds:
                titles.append(ds[0])
                params.append(ds[1])
                widths.append(ds[2])

        h_format = workbook.add_format()
        h_format.set_bold()
        h_format.set_border()
        h_format.set_align('center')
        h_format.set_align('vcenter')
        h_format.set_bg_color('#eeeeee')

        # Adjust the column width.
        for i, col_width in enumerate(widths):
            worksheet.set_column(i, i, col_width)

        us_cnt = 2 if project.is_unit_set else 0  # 동호 지정 시 추가 열 수 계산

        # Write header - 1
        for col_num, title in enumerate(titles):
            if col_num == 5 + us_cnt:
                worksheet.merge_range(row_num, col_num, row_num, col_num + 2, '건별 수납 정보', h_format)
            elif col_num in [6 + us_cnt, 7 + us_cnt]:
                pass
            else:
                worksheet.write(row_num, col_num, title, h_format)

        # Write Header - 2
        row_num = 3
        for col_num, title in enumerate(titles):
            if col_num in [5 + us_cnt, 6 + us_cnt, 7 + us_cnt]:
                worksheet.write(row_num, col_num, title, h_format)
            else:
                worksheet.merge_range(row_num - 1, col_num, row_num, col_num, title, h_format)

        # 4. Body
        # Get some data to write to the spreadsheet.
        og = request.GET.get('og')
        ut = request.GET.get('ut')
        ipo = request.GET.get('ipo')
        ba = request.GET.get('ba')
        nc = request.GET.get('nc')
        ni = request.GET.get('ni')
        q = request.GET.get('q')

        obj_list = ProjectCashBook.objects.filter(project=project,
                                                  income__isnull=False,
                                                  project_account_d3__is_payment=True,
                                                  deal_date__range=(sd, ed)).order_by('deal_date', 'created')

        obj_list = obj_list.filter(contract__order_group=og) if og else obj_list
        obj_list = obj_list.filter(contract__unit_type=ut) if ut else obj_list
        obj_list = obj_list.filter(installment_order_id=ipo) if ipo else obj_list
        obj_list = obj_list.filter(bank_account__id=ba) if ba else obj_list
        obj_list = obj_list.filter(contract__isnull=True) if nc else obj_list
        obj_list = obj_list.filter(installment_order__isnull=True, contract__isnull=False) if ni else obj_list
        obj_list = obj_list.filter(
            Q(contract__contractor__name__icontains=q) |
            Q(content__icontains=q) |
            Q(trader__icontains=q) |
            Q(note__icontains=q)) if q else obj_list

        data = obj_list.values_list(*params)

        # Turn off the warnings:
        worksheet.ignore_errors({'number_stored_as_text': 'C:F'})

        # Default CSS setting
        body_format = {
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': 'yyyy-mm-dd'
        }

        # Write header
        for i, row in enumerate(data):
            row_num += 1

            for col_num, cell_data in enumerate(row):
                if col_num == 0 or col_num == 11:
                    body_format['num_format'] = 'yyyy-mm-dd'
                else:
                    body_format['num_format'] = 41

                bformat = workbook.add_format(body_format)

                worksheet.write(row_num, col_num, cell_data, bformat)

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = '{date}-payments.xlsx'.format(date=ed)
        file_format = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = HttpResponse(output, content_type=file_format)
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response


class ExportPaymentsByCont(View):
    """계약자별 수납내역 리스트"""

    @staticmethod
    def get(request):

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('계약자별_납부내역')

        worksheet.set_default_row(20)

        # ----------------- get_queryset start ----------------- #
        project = Project.objects.get(pk=request.GET.get('project'))
        date = request.GET.get('date')
        date = TODAY if not date or date == 'null' else date
        # ----------------- get_queryset finish ----------------- #
        # 현재 납부 회차 구하기
        now_date = datetime.date.today()
        pay_orders = InstallmentPaymentOrder.objects.filter(project=project)
        now_order = pay_orders.first()
        for o in pay_orders:
            if o.pay_due_date is None or o.pay_due_date <= now_date:
                now_order = o
            else:
                break

        # get pay order
        max_order = ProjectCashBook.objects \
            .filter(project=project, installment_order__isnull=False) \
            .order_by('-installment_order').first().installment_order  # 실제 납부 최대 회차
        calc_order = now_order if now_order.pay_code >= max_order.pay_code else max_order  # 금회차 -> 선납자가 있을 경우 선납회차
        due_pay_orders = pay_orders.filter(project=project, id__lte=calc_order.id)

        add_order_cols = now_order.pay_code * 2  # 납부회차 * 2

        col_cnt = 7 + add_order_cols  # 기본 컬럼수 + 납부회차 * 2
        is_us_cn = 2 if project.is_unit_set else 0  # 동호 표시할 경우 2라인 추가
        if project.is_unit_set:
            col_cnt += is_us_cn

        # 1. Title
        row_num = 0
        title_format = workbook.add_format()
        worksheet.set_row(row_num, 50)
        title_format.set_font_size(18)
        title_format.set_align('vcenter')
        title_format.set_bold()
        worksheet.merge_range(row_num, 0, row_num, col_cnt, str(project) + ' 계약자별 납부내역', title_format)

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, col_cnt, date + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header
        worksheet.set_row(row_num, 25)

        h_format = workbook.add_format()
        h_format.set_bold()
        h_format.set_border()
        h_format.set_align('center')
        h_format.set_align('vcenter')
        h_format.set_bg_color('#eeeeee')

        # Line --------------------- 1
        row_num = 2

        # Write header
        for i in range(col_cnt):
            if i == 0:
                worksheet.merge_range(row_num, i, row_num, i + 2, '계약자 인적사항', h_format)
            elif i == 3:
                worksheet.merge_range(row_num, i, row_num, i + 2 + is_us_cn, '가입 세부사항', h_format)
            elif i == 6 + is_us_cn:
                worksheet.merge_range(row_num, i, row_num, i + 1 + add_order_cols, '분양대금 납부내역', h_format)

        # title_list
        header_src = [
            ['계약번호', 'serial_number', 10],
            ['성명', 'contractor__name', 10],
            ['차수', 'order_group__name', 10],
            ['타입', 'key_unit__unit_type__name', 7],
            ['계약일', 'contractor__contract_date', 12],
            ['기납부 총액', '', 14],
            ['미납내역', '', 13],
        ]

        if project.is_unit_set:
            header_src.insert(4, ['동', 'key_unit__houseunit__building_unit__name', 7])
            header_src.insert(5, ['호수', 'key_unit__houseunit__name', 7])

        # PayOrders columns insert
        for i, po in enumerate(due_pay_orders):
            header_src.insert(6 + (i * 2) + is_us_cn, [po.pay_name, '', 12])
            header_src.insert(7 + (i * 2) + is_us_cn, ['', '', 13])

        titles = ['번호']
        params = ['pk']
        widths = [7]

        for header in header_src:  # 요청된 컬럼 개수 만큼 반복 (1-2-3... -> i)
            titles.append(header[0])  # 일련번호
            params.append(header[1])  # serial_number
            widths.append(header[2])  # 10

        while '' in params:
            params.remove('')

        # Adjust the column width.
        for i, cw in enumerate(widths):  # 각 컬럼 넙이 세팅
            worksheet.set_column(i, i, cw)

        # Line --------------------- 2
        row_num = 3
        worksheet.set_row(row_num, 23)

        # Write header
        digit_col = []  # 숫자(#,##0) 서식 적용 컬럼
        date_col = []  # 날짜(yyyy-mm-dd) 서식 적용 컬럼

        sum_col = None  # 기납부총액 컬럼 위치

        for col_num, title in enumerate(titles):  # 헤더 줄 제목 세팅
            if col_num < 7 + is_us_cn or col_num == col_cnt:
                worksheet.merge_range(row_num, col_num, row_num + 1, col_num, title, h_format)
            else:
                if col_num % 2 == 1:
                    worksheet.merge_range(row_num, col_num, row_num, col_num + 1, title, h_format)
            if title == '계약일':
                date_col.append(col_num)
            if title in ('기납부 총액', '미납내역'):
                digit_col.append(col_num)
                if title == '기납부 총액':
                    sum_col = col_num

        # Line --------------------- 3
        row_num = 4
        worksheet.set_row(row_num, 23)

        for col_num in range(col_cnt):
            if col_num <= 7 + is_us_cn or col_num < col_cnt:
                worksheet.write(row_num, col_num, ('금액', '거래일')[col_num % 2], h_format)
                if col_num % 2:
                    date_col.append(col_num)
                else:
                    digit_col.append(col_num)

        # 4. Body
        body_format = {
            'border': True,
            'valign': 'vcenter',
            'num_format': '#,##0',
            'align': 'center',
        }

        # Turn off some of the warnings:
        worksheet.ignore_errors({'number_stored_as_text': 'E:G'})

        # ----------------- get_queryset start ----------------- #
        # Get some data to write to the spreadsheet.
        obj_list = Contract.objects.filter(project=project,
                                           activation=True,
                                           contractor__status='2',
                                           contractor__contract_date__lte=date) \
            .order_by('contractor__contract_date', 'created')

        # ----------------- get_queryset finish ----------------- #

        data = obj_list.values_list(*params)

        # Write body
        # ----------------------------------------------------------------- #
        paid_params = ['contract', 'income', 'installment_order', 'deal_date']
        paid_data = ProjectCashBook.objects.filter(project=project,
                                                   income__isnull=False,
                                                   project_account_d3__is_payment=True,
                                                   deal_date__lte=date,
                                                   contract__isnull=False)
        paid_dict = paid_data.values_list(*paid_params)

        # 계약금 분납 횟수
        down_num = due_pay_orders.filter(pay_sort='1').count()
        # ----------------------------------------------------------------- #

        for i, row in enumerate(data):
            row_num += 1
            row = list(row)  # tuple -> list

            paid_sum = 0  # 기납부 총액
            if sum_col is not None:
                paid_sum = sum([ps[1] for ps in paid_dict if ps[0] == row[0]])
                row.insert(sum_col, paid_sum)  # 순서 삽입

            next_col = sum_col
            due_amt_sum = 0  # 납부 약정액 합계
            unpaid_amt = 0  # 미납액

            contract = Contract.objects.get(serial_number=row[1], contractor__name=row[2])
            prices = SalesPriceByGT.objects.filter(project_id=project,
                                                   order_group__name=row[3],
                                                   unit_type__name=row[4])
            try:
                floor = contract.key_unit.houseunit.floor_type
                cont_price = prices.get(unit_floor_type=floor).price  # 분양가
            except ObjectDoesNotExist:
                cont_price = ProjectIncBudget.objects.get(order_group__name=row[3],
                                                          unit_type__name=row[4]).average_price
            except ProjectIncBudget.DoesNotExsist:
                price = contract.key_unit.unit_type.average_price
                cont_price = price if price else 0  # 분양가

            for pi, po in enumerate(due_pay_orders):  # 회차별 납입 내역 삽입
                dates = [p[3] for p in paid_dict if p[0] == row[0] and p[2] == po.pay_code]
                paid_date = max(dates).strftime('%Y-%m-%d') if dates else None
                paid_amount = sum([p[1] for p in paid_dict if p[0] == row[0] and p[2] == po.pay_code])

                row.insert(next_col + 1 + pi, paid_date)  # 거래일 정보 삽입
                row.insert(next_col + 2 + pi, paid_amount)  # 납부 금액 정보 삽입

                # due_amount adding
                if po.pay_sort == '1':  # 계약금일 때
                    try:
                        down_pay = DownPayment.objects.get(
                            project_id=project,
                            order_group=contract.order_group,
                            unit_type=contract.key_unit.unit_type)
                        due_amt = down_pay.payment_amount
                    except DownPayment.DoesNotExist:
                        pn = round(down_num / 2)
                        due_amt = int(cont_price * 0.1 / pn)
                elif po.pay_sort == '2':  # 중도금일 때
                    due_amt = cont_price * 0.1
                else:  # 잔금일 때
                    due_amt = cont_price - due_amt_sum

                due_amt_sum += due_amt if po.id <= now_order.id else 0
                unpaid_amt = due_amt_sum - paid_sum if due_amt_sum > paid_sum else 0
                next_col += 1

            row.insert(next_col + len(due_pay_orders) + 1, unpaid_amt)  # 미납 내역 삽입

            row[0] = i + 1  # pk 대신 순서 삽입

            for col_num, cell_data in enumerate(row):
                # css 설정
                if col_num <= 4 + is_us_cn:
                    body_format['num_format'] = '#,##0'
                elif col_num in date_col:  # 날짜 컬럼 일때
                    body_format['num_format'] = 'yyyy-mm-dd'
                elif col_num in digit_col:  # 숫자(금액) 컬럼 일때
                    body_format['num_format'] = 41

                bf = workbook.add_format(body_format)

                worksheet.write(row_num, col_num, cell_data, bf)

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = f'{date}-payment-by-cont.xlsx'
        file_format = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = HttpResponse(output, content_type=file_format)
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response


class ExportPaymentStatus(View):
    """차수 및 타입별 수납 집계 현황"""

    @staticmethod
    def get(request):

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('차수_타입별_수납집계')

        worksheet.set_default_row(20)

        # ----------------- get_queryset start ----------------- #
        project = Project.objects.get(pk=request.GET.get('project'))
        date = request.GET.get('date')
        # ----------------- get_queryset finish ----------------- #

        rows_cnt = 9

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)
        title_format = workbook.add_format()
        title_format.set_bold()
        title_format.set_font_size(18)
        title_format.set_align('vcenter')
        worksheet.merge_range(row_num, 0, row_num, rows_cnt, str(project) + ' 차수 및 타입별 수납 현황', title_format)

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, rows_cnt, date + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header
        row_num = 2
        worksheet.set_row(row_num, 23)

        h_format = {
            'bold': True,
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#eeeeee',
        }

        # Header_contents - Vue 컴포넌트와 동일한 구조
        header_src = [['차수', 'order_group', 13],
                      ['타입', 'unit_type', 13],
                      ['전체매출액', 'total_sales_amount', 18],
                      ['계약 현황', '', 11],
                      ['', '', 18],
                      ['', '', 18],
                      ['', '', 18],
                      ['미계약세대수', 'non_contract_units', 13],
                      ['미계약금액', 'non_contract_amount', 18],
                      ['합계', 'total_budget', 18]]

        titles = []  # 헤더명
        params = []  # 헤더 컬럼(db)
        widths = []  # 헤더 넓이

        for ds in header_src:
            if ds:
                titles.append(ds[0])
                params.append(ds[1])
                widths.append(ds[2])

        while '' in params:
            params.remove('')

        # Adjust the column width.
        for i, col_width in enumerate(widths):  # 각 컬럼 넓이 세팅
            worksheet.set_column(i, i, col_width)

        # Write header
        h1format = workbook.add_format(h_format)

        for col_num, title in enumerate(titles):
            worksheet.write(row_num, col_num, title, h1format)

        # Write header
        cont_col_num = (3, 4, 5, 6)  # 계약 현황 관련 컬럼들

        for col_num, title in enumerate(titles):  # 헤더 줄 제목 세팅
            if int(col_num) == 3:  # 계약 현황
                worksheet.merge_range(row_num, col_num, row_num, col_num + 3, title, h1format)
            elif int(col_num) not in cont_col_num:
                worksheet.merge_range(row_num, col_num, row_num + 1, col_num, title, h1format)

        row_num = 3
        worksheet.set_row(row_num, 23)

        for col_num, col in enumerate(titles):
            if int(col_num) == 3:  # 계약 현황
                worksheet.write(row_num, col_num, '계약세대수', h1format)
            if int(col_num) == 4:
                worksheet.write(row_num, col_num, '계약금액', h1format)
            if int(col_num) == 5:
                worksheet.write(row_num, col_num, '실수납금액', h1format)
            if int(col_num) == 6:
                worksheet.write(row_num, col_num, '미수금액', h1format)

        # 4. Body
        # Get some data to write to the spreadsheet.

        body_format = {
            'border': True,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '_-* #,##0_-;-* #,##0_-;_-* "-"_-;_-@_-'
        }

        # Turn off some of the warnings:
        worksheet.ignore_errors({'number_stored_as_text': 'B:C'})

        # ----------------- get_data_using_api start ----------------- #
        # PaymentStatusByUnitTypeViewSet와 동일한 로직 사용
        from unittest.mock import Mock

        # Mock request 객체 생성
        mock_request = Mock()
        mock_request.query_params = {
            'project': str(project.pk),
            'date': date if date else 'null'
        }

        # API ViewSet의 list 메서드 호출
        viewset = PaymentStatusByUnitTypeViewSet()
        response = viewset.list(mock_request)
        api_data = response.data

        # ----------------- get_data_using_api finish ----------------- #

        # Helper function for order_group row spanning
        def get_og_item_count(order_group_id):
            return len([item for item in api_data if item['order_group_id'] == order_group_id])

        def is_first_type_in_order_group(item):
            same_order_group_items = [d for d in api_data if d['order_group_id'] == item['order_group_id']]
            return same_order_group_items[0]['unit_type_id'] == item['unit_type_id']

        # 합계 계산
        totals = {
            'total_sales_amount': sum(item['total_sales_amount'] for item in api_data),
            'contract_units': sum(item['contract_units'] for item in api_data),
            'contract_amount': sum(item['contract_amount'] for item in api_data),
            'paid_amount': sum(item['paid_amount'] for item in api_data),
            'unpaid_amount': sum(item['unpaid_amount'] for item in api_data),
            'non_contract_units': sum(item['non_contract_units'] for item in api_data),
            'non_contract_amount': sum(item['non_contract_amount'] for item in api_data),
            'total_budget': sum(item['total_budget'] for item in api_data),
        }

        # Write data - API 데이터 사용
        for item in api_data:
            row_num += 1

            for col_num, title in enumerate(titles):
                # css 정렬
                if col_num <= 1:
                    body_format['align'] = 'center'
                else:
                    body_format['num_format'] = '_-* #,##0_-;-* #,##0_-;_-* "-"_-;_-@_-'

                bformat = workbook.add_format(body_format)

                type_count = get_og_item_count(item['order_group_id']) - 1

                if col_num == 0 and is_first_type_in_order_group(item):
                    # 차수명 (행 병합)
                    worksheet.merge_range(row_num, col_num, row_num + type_count, col_num, item['order_group_name'],
                                          bformat)
                elif col_num == 1:
                    # 타입명
                    worksheet.write(row_num, col_num, item['unit_type_name'], bformat)
                elif col_num == 2:
                    # 전체매출액
                    worksheet.write(row_num, col_num, item['total_sales_amount'], bformat)
                elif col_num == 3:
                    # 계약 세대수
                    worksheet.write(row_num, col_num, item['contract_units'], bformat)
                elif col_num == 4:
                    # 계약 금액
                    worksheet.write(row_num, col_num, item['contract_amount'], bformat)
                elif col_num == 5:
                    # 실수납 금액
                    worksheet.write(row_num, col_num, item['paid_amount'], bformat)
                elif col_num == 6:
                    # 미수 금액
                    worksheet.write(row_num, col_num, item['unpaid_amount'], bformat)
                elif col_num == 7:
                    # 미계약 세대수
                    worksheet.write(row_num, col_num, item['non_contract_units'], bformat)
                elif col_num == 8:
                    # 미계약 금액
                    worksheet.write(row_num, col_num, item['non_contract_amount'], bformat)
                elif col_num == 9:
                    # 합계
                    worksheet.write(row_num, col_num, item['total_budget'], bformat)

        row_num += 1
        worksheet.set_row(row_num, 23)

        # 합계 행 작성 - API 데이터 기반
        for col_num, col in enumerate(titles):
            # css 정렬
            if col_num == 0:
                h_format['align'] = 'center'
            else:
                h_format['num_format'] = '_-* #,##0_-;-* #,##0_-;_-* "-"_-;_-@_-'

            h2format = workbook.add_format(h_format)

            if col_num == 0:
                worksheet.merge_range(row_num, col_num, row_num, col_num + 1, '합계', h2format)
            elif col_num == 2:
                # 전체매출액 합계
                worksheet.write(row_num, col_num, totals['total_sales_amount'], h2format)
            elif col_num == 3:
                # 계약 세대수 합계
                worksheet.write(row_num, col_num, totals['contract_units'], h2format)
            elif col_num == 4:
                # 계약 금액 합계
                worksheet.write(row_num, col_num, totals['contract_amount'], h2format)
            elif col_num == 5:
                # 실수납 금액 합계
                worksheet.write(row_num, col_num, totals['paid_amount'], h2format)
            elif col_num == 6:
                # 미수 금액 합계
                worksheet.write(row_num, col_num, totals['unpaid_amount'], h2format)
            elif col_num == 7:
                # 미계약 세대수 합계
                worksheet.write(row_num, col_num, totals['non_contract_units'], h2format)
            elif col_num == 8:
                # 미계약 금액 합계
                worksheet.write(row_num, col_num, totals['non_contract_amount'], h2format)
            elif col_num == 9:
                # 합계 (총 예산)
                worksheet.write(row_num, col_num, totals['total_budget'], h2format)

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = '{this_date}-payment-status.xlsx'.format(this_date=date)
        file_format = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = HttpResponse(output, content_type=file_format)
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response


class ExportOverallSummary(View):
    """총괄 집계 현황"""

    @staticmethod
    def get(request):

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('총괄_집계_현황')

        worksheet.set_default_row(20)

        # ----------------- get_queryset start ----------------- #
        project = Project.objects.get(pk=request.GET.get('project'))
        date = request.GET.get('date')
        # ----------------- get_queryset finish ----------------- #

        # ----------------- get_data_using_api start ----------------- #
        # OverallSummaryViewSet와 동일한 로직 사용
        from unittest.mock import Mock

        # Mock request 객체 생성
        mock_request = Mock()
        mock_request.query_params = {
            'project': str(project.pk),
            'date': date if date else 'null'
        }

        # API ViewSet의 list 메서드 호출
        viewset = OverallSummaryViewSet()
        response = viewset.list(mock_request)
        api_data = response.data

        pay_orders = api_data.get('pay_orders', [])
        aggregate_data = api_data.get('aggregate', {})

        # ----------------- get_data_using_api finish ----------------- #

        # 동적 컬럼 수 계산 (빈열 + 구분열 + 납부회차들 + 계열)
        col_count = 2 + len(pay_orders) + 1

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)
        title_format = workbook.add_format()
        title_format.set_bold()
        title_format.set_font_size(18)
        title_format.set_align('vcenter')
        worksheet.merge_range(row_num, 0, row_num, col_count - 1, str(project) + ' 총괄 집계 현황', title_format)

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, col_count - 1, date + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header
        row_num = 2
        worksheet.set_row(row_num, 23)

        h_format = {
            'bold': True,
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#eeeeee',
        }

        # 컬럼 너비 설정
        worksheet.set_column(0, 0, 12)  # 빈 열
        worksheet.set_column(1, 1, 15)  # 구분 열
        for i in range(len(pay_orders)):
            worksheet.set_column(2 + i, 2 + i, 15)  # 각 납부회차 열
        worksheet.set_column(col_count - 1, col_count - 1, 18)  # 계 열

        h1format = workbook.add_format(h_format)

        # Write main header
        worksheet.write(row_num, 0, '', h1format)  # 빈 열
        worksheet.write(row_num, 1, '구분', h1format)

        # 납부회차 헤더들
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['pay_name'], h1format)

        worksheet.write(row_num, col_count - 1, '계', h1format)

        # 4. 약정일 행
        row_num = 3
        worksheet.set_row(row_num, 20)

        due_date_format = workbook.add_format({
            'border': True,
            'align': 'center',
            'valign': 'vcenter'
        })

        worksheet.write(row_num, 0, '기본', due_date_format)
        worksheet.write(row_num, 1, '약정일', due_date_format)

        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order.get('pay_due_date', ''), due_date_format)

        worksheet.write(row_num, col_count - 1, '', due_date_format)

        # 5. Body - 계약 섹션 (4행)
        body_format = {
            'border': True,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '_-* #,##0_-;-* #,##0_-;_-* "-"_-;_-@_-'
        }

        center_format = {
            'border': True,
            'align': 'center',
            'valign': 'vcenter'
        }

        # 계약 섹션 - 계약
        row_num += 1
        worksheet.merge_range(row_num, 0, row_num + 3, 0, '계약', workbook.add_format({**center_format, **h_format}))

        # 계약(세대수)
        worksheet.write(row_num, 1, f'계약({aggregate_data.get("conts_num", 0):,})', workbook.add_format(center_format))
        total_contract_amount = sum(order['contract_amount'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['contract_amount'], workbook.add_format(body_format))
        worksheet.write(row_num, col_count - 1, total_contract_amount, workbook.add_format(body_format))

        # 미계약(세대수)
        row_num += 1
        worksheet.write(row_num, 1, f'미계약({aggregate_data.get("non_conts_num", 0):,})',
                        workbook.add_format(center_format))
        total_non_contract_amount = sum(order['non_contract_amount'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['non_contract_amount'], workbook.add_format(body_format))
        worksheet.write(row_num, col_count - 1, total_non_contract_amount, workbook.add_format(body_format))

        # 총계(세대수)
        row_num += 1
        worksheet.write(row_num, 1, f'총계({aggregate_data.get("total_units", 0):,})', workbook.add_format(center_format))
        total_amount = total_contract_amount + total_non_contract_amount
        for i, order in enumerate(pay_orders):
            total_per_order = order['contract_amount'] + order['non_contract_amount']
            worksheet.write(row_num, 2 + i, total_per_order, workbook.add_format(body_format))
        worksheet.write(row_num, col_count - 1, total_amount, workbook.add_format(body_format))

        # 계약율
        row_num += 1
        worksheet.write(row_num, 1, '계약율', workbook.add_format(center_format))
        contract_rate = float(aggregate_data.get('contract_rate', 0))
        percent_format = workbook.add_format({**body_format, 'num_format': '_-* 0.00%_-;-* 0.00%_-;_-* "-"??%_-;_-@_-'})
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, contract_rate / 100, percent_format)
        worksheet.write(row_num, col_count - 1, contract_rate / 100, percent_format)

        # 6. 수납 섹션 (5행)
        row_num += 1
        worksheet.merge_range(row_num, 0, row_num + 4, 0, '수납', workbook.add_format({**center_format, **h_format}))

        # 수납액
        worksheet.write(row_num, 1, '수납액', workbook.add_format(center_format))
        total_collected_amount = sum(order['collection']['collected_amount'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['collection']['collected_amount'], workbook.add_format(body_format))
        worksheet.write(row_num, col_count - 1, total_collected_amount, workbook.add_format(body_format))

        # 할인료
        row_num += 1
        worksheet.write(row_num, 1, '할인료', workbook.add_format(center_format))
        total_discount_amount = sum(order['collection']['discount_amount'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['collection']['discount_amount'], workbook.add_format(body_format))
        worksheet.write(row_num, col_count - 1, total_discount_amount, workbook.add_format(body_format))

        # 연체료
        row_num += 1
        worksheet.write(row_num, 1, '연체료', workbook.add_format(center_format))
        total_overdue_fee = sum(order['collection']['overdue_fee'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['collection']['overdue_fee'], workbook.add_format(body_format))
        worksheet.write(row_num, col_count - 1, total_overdue_fee, workbook.add_format(body_format))

        # 실수납액
        row_num += 1
        worksheet.write(row_num, 1, '실수납액', workbook.add_format(center_format))
        total_actual_collected = sum(order['collection']['actual_collected'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['collection']['actual_collected'], workbook.add_format(body_format))
        worksheet.write(row_num, col_count - 1, total_actual_collected, workbook.add_format(body_format))

        # 수납율
        row_num += 1
        worksheet.write(row_num, 1, '수납율', workbook.add_format(center_format))
        total_collection_rate = (
                total_actual_collected / total_contract_amount * 100) if total_contract_amount > 0 else 0
        for i, order in enumerate(pay_orders):
            collection_rate = float(order['collection']['collection_rate'])
            worksheet.write(row_num, 2 + i, collection_rate / 100, percent_format)
        worksheet.write(row_num, col_count - 1, total_collection_rate / 100, percent_format)

        # 7. 기간도래 섹션 (5행)
        row_num += 1
        worksheet.merge_range(row_num, 0, row_num + 4, 0, '기간도래', workbook.add_format({**center_format, **h_format}))

        # 약정금액
        worksheet.write(row_num, 1, '약정금액', workbook.add_format(center_format))
        total_due_contract_amount = sum(order['due_period']['contract_amount'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['due_period']['contract_amount'], workbook.add_format(body_format))
        worksheet.write(row_num, col_count - 1, total_due_contract_amount, workbook.add_format(body_format))

        # 미수금
        row_num += 1
        worksheet.write(row_num, 1, '미수금', workbook.add_format(center_format))
        total_due_unpaid_amount = sum(order['due_period']['unpaid_amount'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['due_period']['unpaid_amount'], workbook.add_format(body_format))
        worksheet.write(row_num, col_count - 1, total_due_unpaid_amount, workbook.add_format(body_format))

        # 미수율
        row_num += 1
        worksheet.write(row_num, 1, '미수율', workbook.add_format(center_format))
        total_due_unpaid_rate = (
                total_due_unpaid_amount / total_due_contract_amount * 100) if total_due_contract_amount > 0 else 0
        for i, order in enumerate(pay_orders):
            unpaid_rate = float(order['due_period']['unpaid_rate'])
            worksheet.write(row_num, 2 + i, unpaid_rate / 100, percent_format)
        worksheet.write(row_num, col_count - 1, total_due_unpaid_rate / 100, percent_format)

        # 연체료
        row_num += 1
        worksheet.write(row_num, 1, '연체료', workbook.add_format(center_format))
        total_due_overdue_fee = sum(order['due_period']['overdue_fee'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['due_period']['overdue_fee'], workbook.add_format(body_format))
        worksheet.write(row_num, col_count - 1, total_due_overdue_fee, workbook.add_format(body_format))

        # 소계
        row_num += 1
        worksheet.write(row_num, 1, '소계', workbook.add_format(center_format))
        total_due_subtotal = sum(order['due_period']['subtotal'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['due_period']['subtotal'], workbook.add_format(body_format))
        worksheet.write(row_num, col_count - 1, total_due_subtotal, workbook.add_format(body_format))

        # 8. 기간미도래 섹션 (1행)
        row_num += 1
        worksheet.write(row_num, 0, '기간미도래', workbook.add_format({**center_format, **h_format}))
        worksheet.write(row_num, 1, '미수금', workbook.add_format(center_format))
        total_not_due_unpaid = sum(order['not_due_unpaid'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['not_due_unpaid'], workbook.add_format(body_format))
        worksheet.write(row_num, col_count - 1, total_not_due_unpaid, workbook.add_format(body_format))

        # 9. 총계 섹션 (2행)
        row_num += 1
        worksheet.merge_range(row_num, 0, row_num + 1, 0, '총계', workbook.add_format({**center_format, **h_format}))

        # 미수금
        worksheet.write(row_num, 1, '미수금', workbook.add_format(center_format))
        total_total_unpaid = sum(order['total_unpaid'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['total_unpaid'], workbook.add_format(body_format))
        worksheet.write(row_num, col_count - 1, total_total_unpaid, workbook.add_format(body_format))

        # 미수율
        row_num += 1
        worksheet.write(row_num, 1, '미수율', workbook.add_format(center_format))
        total_total_unpaid_rate = (total_total_unpaid / (total_contract_amount + total_non_contract_amount) * 100) if (
                                                                                                                              total_contract_amount + total_non_contract_amount) > 0 else 0
        for i, order in enumerate(pay_orders):
            total_unpaid_rate = float(order['total_unpaid_rate'])
            worksheet.write(row_num, 2 + i, total_unpaid_rate / 100, percent_format)
        worksheet.write(row_num, col_count - 1, total_total_unpaid_rate / 100, percent_format)

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = '{this_date}-overall-summary.xlsx'.format(this_date=date)
        file_format = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = HttpResponse(output, content_type=file_format)
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response
