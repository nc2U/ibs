"""
Payment Excel Export Views

납부 관련 Excel 내보내기 뷰들
"""
import datetime
from unittest.mock import Mock

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, Sum

from _excel.mixins import ExcelExportMixin, ProjectFilterMixin, AdvancedExcelMixin
from apiV1.views.payment import PaymentStatusByUnitTypeViewSet, OverallSummaryViewSet
from cash.models import ProjectCashBook
from contract.models import Contract
from payment.models import InstallmentPaymentOrder, SalesPriceByGT, DownPayment
from project.models import ProjectIncBudget

TODAY = datetime.date.today().strftime('%Y-%m-%d')


def get_standardized_payment_sum(project, date=None, date_range=None):
    """
    표준화된 납부액 집계 (유효 계약자 입금만)

    payment_records() 사용으로 일관된 집계 기준 적용:
    - is_payment=True (111, 811 계정만)
    - 유효 계약만 (activation=True)
    - select_related 최적화 포함
    """
    queryset = ProjectCashBook.objects.payment_records().filter(
        project=project,
        contract__isnull=False,
        contract__activation=True
    )

    if date_range:
        # ExportPayments용 날짜 범위
        queryset = queryset.filter(deal_date__range=date_range)
    elif date:
        # ExportPaymentsByCont, ExportPaymentStatus용 특정 날짜까지
        queryset = queryset.filter(deal_date__lte=date)

    return queryset.aggregate(total=Sum('income'))['total'] or 0


def get_standardized_payment_sum_by_order(project, date, installment_order_id):
    """
    회차별 표준화된 납부액 집계 (유효 계약자 입금만)

    payment_records() 사용으로 일관된 집계 기준 적용
    """
    return (
        ProjectCashBook.objects
        .payment_records()
        .filter(
            project=project,
            installment_order_id=installment_order_id,
            contract__isnull=False,
            contract__activation=True,
            deal_date__lte=date
        )
        .aggregate(total=Sum('income'))['total'] or 0
    )


class ExportPayments(ExcelExportMixin, ProjectFilterMixin, AdvancedExcelMixin):
    """수납건별 수납내역 리스트 (Mixins 사용)"""

    def get(self, request):
        # Get project and date parameters
        project = self.get_project(request)
        if not project:
            raise ValueError("Project ID is required")

        sd = request.GET.get('sd', '1900-01-01')
        ed = request.GET.get('ed', TODAY)

        # Create a workbook with performance optimization
        output, workbook, worksheet = self.create_workbook('수납건별_납부내역')

        # Create reusable format objects
        formats = self.create_format_objects(workbook)

        # Define headers
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

        # Set column widths
        widths = [h[2] for h in header_src]
        self.set_column_widths(worksheet, widths)

        # Write title
        row_num = 0
        col_count = len(header_src) - 1
        row_num = self.write_title(worksheet, workbook, row_num, col_count,
                                   f'{project} 계약자 대금 납부내역')

        # Write date info
        row_num = self.write_date_info(worksheet, workbook, row_num, col_count,
                                       ed, formats['right_align'])

        # Write complex headers
        row_num = self._write_payment_headers(worksheet, workbook, row_num, header_src,
                                              project.is_unit_set, formats)

        # Get and write data
        data = self._get_payment_data(request, project, sd, ed, header_src)
        self._write_payment_data(worksheet, workbook, row_num, data, formats, project, header_src)

        # Create response
        filename = request.GET.get('filename') or 'payments'
        filename = f'{filename}-{ed}'
        return self.create_response(output, workbook, filename)

    @staticmethod
    def _write_payment_headers(worksheet, workbook, row_num, header_src, is_unit_set, formats):
        """납부 내역 전용 복잡한 헤더 작성"""
        titles = [h[0] for h in header_src]
        us_cnt = 2 if is_unit_set else 0

        # Header level 1
        worksheet.set_row(row_num, 20)
        for col_num, title in enumerate(titles):
            if col_num == 5 + us_cnt:
                worksheet.merge_range(row_num, col_num, row_num, col_num + 2,
                                      '건별 수납 정보', formats['header'])
            elif col_num not in [6 + us_cnt, 7 + us_cnt]:
                worksheet.write(row_num, col_num, title, formats['header'])

        # Header level 2
        row_num += 1
        for col_num, title in enumerate(titles):
            if col_num in [5 + us_cnt, 6 + us_cnt, 7 + us_cnt]:
                worksheet.write(row_num, col_num, title, formats['header'])
            else:
                worksheet.merge_range(row_num - 1, col_num, row_num, col_num,
                                      title, formats['header'])

        return row_num + 1

    @staticmethod
    def _get_payment_data(request, project, sd, ed, header_src):
        """납부 데이터 조회"""
        params = [h[1] for h in header_src]

        # Filter parameters
        og = request.GET.get('og')
        ut = request.GET.get('ut')
        ipo = request.GET.get('ipo')
        ba = request.GET.get('ba')
        nc = request.GET.get('nc')
        ni = request.GET.get('ni')
        q = request.GET.get('q')

        # 유효 계약자 납부내역 조회 (payment_records 사용)
        obj_list = (
            ProjectCashBook.objects
            .payment_records()  # is_payment=True, select_related 최적화 포함
            .filter(
                project=project,
                deal_date__range=(sd, ed),
                contract__isnull=False,
                contract__activation=True  # 유효 계약만
            )
            .order_by('deal_date', 'created')
        )

        # Apply filters
        if og:
            obj_list = obj_list.filter(contract__order_group=og)
        if ut:
            obj_list = obj_list.filter(contract__unit_type=ut)
        if ipo:
            obj_list = obj_list.filter(installment_order_id=ipo)
        if ba:
            obj_list = obj_list.filter(bank_account__id=ba)
        if nc:
            obj_list = obj_list.filter(contract__isnull=True)
        if ni:
            obj_list = obj_list.filter(installment_order__isnull=True, contract__isnull=False)
        if q:
            obj_list = obj_list.filter(
                Q(contract__contractor__name__icontains=q) |
                Q(content__icontains=q) |
                Q(trader__icontains=q) |
                Q(note__icontains=q)
            )

        return obj_list.values_list(*params)

    @staticmethod
    def _write_payment_data(worksheet, workbook, row_num, data, formats, project, header_src):
        """납부 데이터 작성"""
        worksheet.ignore_errors({'number_stored_as_text': 'C:F'})

        # 헤더 이름으로 컬럼 위치 찾기
        header_names = [h[0] for h in header_src]

        # 각 컬럼의 인덱스 찾기
        date_columns = []
        currency_columns = []

        for i, header_name in enumerate(header_names):
            if '일자' in header_name or '날짜' in header_name or '체결일' in header_name:
                date_columns.append(i)
            elif '금액' in header_name:
                currency_columns.append(i)

        for i, row in enumerate(data):
            for col_num, cell_data in enumerate(row):
                # Select format based on column type
                if col_num in date_columns:
                    cell_format = formats['date']
                elif col_num in currency_columns:
                    cell_format = formats['currency']
                else:
                    cell_format = formats['default']

                worksheet.write(row_num, col_num, cell_data, cell_format)
            row_num += 1


class ExportPaymentsByCont(ExcelExportMixin, ProjectFilterMixin, AdvancedExcelMixin):
    """계약자별 수납내역 리스트 (Mixins 사용)"""

    def get(self, request):
        # Get project and date parameters using mixins
        project = self.get_project(request)
        if not project:
            raise ValueError("Project ID is required")

        date = request.GET.get('to_date', TODAY)

        # Create a workbook with performance optimization
        output, workbook, worksheet = self.create_workbook('계약자별_납부내역', in_memory=False)

        # Create reusable format objects
        formats = self.create_format_objects(workbook)
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

        # Write title using mixin
        row_num = 0
        row_num = self.write_title(worksheet, workbook, row_num, col_cnt,
                                   f'{project} 계약자별 납부내역')

        # Write date info using mixin
        row_num = self.write_date_info(worksheet, workbook, row_num, col_cnt,
                                       date, formats['right_align'])

        # 3. Header
        worksheet.set_row(row_num, 25)

        # Use header format from mixin
        h_format = formats['header']

        # Line --------------------- 1

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
        # Use pre-created format objects from mixin
        default_body_format = formats['default']
        date_body_format = formats['date']
        digit_body_format = formats['currency']

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
        paid_data = (
            ProjectCashBook.objects
            .payment_records()  # is_payment=True, select_related 최적화
            .filter(
                project=project,
                deal_date__lte=date,
                contract__isnull=False,
                contract__activation=True
            )
        )
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
                # Use pre-created format objects
                if col_num <= 4 + is_us_cn:
                    bf = default_body_format
                elif col_num in date_col:  # 날짜 컬럼 일때
                    bf = date_body_format
                elif col_num in digit_col:  # 숫자(금액) 컬럼 일때
                    bf = digit_body_format
                else:
                    bf = default_body_format

                worksheet.write(row_num, col_num, cell_data, bf)

        # Create a response using mixin\
        filename = request.GET.get('filename') or 'payment-by-cont'
        filename = f'{filename}-{date}'
        return self.create_response(output, workbook, filename)


class ExportPaymentStatus(ExcelExportMixin, ProjectFilterMixin, AdvancedExcelMixin):
    """차수 및 타입별 수납 집계 현황 (Mixins 사용)"""

    def get(self, request):
        # Get project and date parameters using mixins
        project = self.get_project(request)
        if not project:
            raise ValueError("Project ID is required")

        date = request.GET.get('date', TODAY)

        # Create a workbook with performance optimization
        output, workbook, worksheet = self.create_workbook('차수_타입별_수납집계', in_memory=False)

        # Create reusable format objects
        formats = self.create_format_objects(workbook)

        rows_cnt = 9

        # Write title using mixin
        row_num = 0
        row_num = self.write_title(worksheet, workbook, row_num, rows_cnt,
                                   f'{project} 차수 및 타입별 수납 현황')

        # Write date info using mixin
        row_num = self.write_date_info(worksheet, workbook, row_num, rows_cnt,
                                       date, formats['right_align'])

        # 3. Header
        row_num = 2
        worksheet.set_row(row_num, 23)

        # Use header format from mixin
        h_format = formats['header']
        h1format = h_format  # format alias for compatibility

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

        # Set column widths using mixin
        self.set_column_widths(worksheet, widths)

        # Write header
        for col_num, title in enumerate(titles):
            worksheet.write(row_num, col_num, title, h_format)

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

        # Use format objects from mixin
        center_body_format = formats['number']
        right_body_format = formats['currency']

        # Turn off some of the warnings:
        worksheet.ignore_errors({'number_stored_as_text': 'B:C'})

        # ----------------- get_data_using_api start ----------------- #
        # PaymentStatusByUnitTypeViewSet와 동일한 로직 사용
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

        # 개별 차수×타입별 실수납 금액을 표준화된 방식으로 재계산
        for item in api_data:
            # 해당 차수×타입에 대한 표준화된 실수납 금액 계산 (payment_records 사용)
            queryset = (
                ProjectCashBook.objects
                .payment_records()  # is_payment=True, select_related 최적화
                .filter(
                    project=project,
                    contract__isnull=False,
                    contract__activation=True,
                    contract__order_group_id=item['order_group_id'],
                    contract__unit_type_id=item['unit_type_id']
                )
            )

            if date and date != 'null':
                queryset = queryset.filter(deal_date__lte=date)

            standardized_item_paid = queryset.aggregate(
                total=Sum('income')
            )['total'] or 0

            # API 데이터의 paid_amount를 표준화된 값으로 교체
            item['paid_amount'] = standardized_item_paid

            # 미수금액도 재계산: 계약금액 - 표준화된 실수납금액 (음수 포함 - 초과납부 반영)
            item['unpaid_amount'] = item['contract_amount'] - standardized_item_paid

        # 합계 계산 - 표준화된 집계 방식 사용
        standardized_paid_amount = get_standardized_payment_sum(project, date)

        # 합계 계산
        total_contract_amount = sum(item['contract_amount'] for item in api_data)
        standardized_total_unpaid = total_contract_amount - standardized_paid_amount  # 음수 포함 - 초과납부 반영

        totals = {
            'total_sales_amount': sum(item['total_sales_amount'] for item in api_data),
            'contract_units': sum(item['contract_units'] for item in api_data),
            'contract_amount': total_contract_amount,
            'paid_amount': standardized_paid_amount,  # 표준화된 집계 사용
            'unpaid_amount': standardized_total_unpaid,  # 계약금액 - 표준화된 실수납금액
            'non_contract_units': sum(item['non_contract_units'] for item in api_data),
            'non_contract_amount': sum(item['non_contract_amount'] for item in api_data),
            'total_budget': sum(item['total_budget'] for item in api_data),
        }

        # Write data - API 데이터 사용
        for item in api_data:
            row_num += 1

            for col_num, title in enumerate(titles):
                # Use pre-created format objects
                if col_num <= 1:
                    bformat = center_body_format
                else:
                    bformat = right_body_format

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
            # Create a new format for summary row
            if col_num == 0:
                h2format = workbook.add_format({
                    'bold': True,
                    'border': True,
                    'align': 'center',
                    'valign': 'vcenter',
                    'bg_color': '#eeeeee'
                })
            else:
                h2format = workbook.add_format({
                    'bold': True,
                    'border': True,
                    'align': 'center',
                    'valign': 'vcenter',
                    'bg_color': '#eeeeee',
                    'num_format': '_-* #,##0_-;-* #,##0_-;_-* "-"_-;_-@_-'
                })

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

        # Create a response using mixin
        filename = request.GET.get('filename')
        filename = f'{filename}-{date}'
        return self.create_response(output, workbook, filename)


class ExportOverallSummary(ExcelExportMixin, ProjectFilterMixin, AdvancedExcelMixin):
    """총괄 집계 현황"""

    def get(self, request):

        # Create a workbook using mixin
        output, workbook, worksheet = self.create_workbook('총괄_집계_현황')

        # Get project using mixin
        project = self.get_project(request)
        date = request.GET.get('date', TODAY)

        # ----------------- get_data_using_api start ----------------- #
        # OverallSummaryViewSet와 동일한 로직 사용
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

        # Get format objects from mixin
        formats = self.create_format_objects(workbook)

        # 1. Title
        title = str(project) + ' 총괄 집계 현황'
        row_num = self.write_title(worksheet, workbook, 0, col_count - 1, title)

        # 2. Date
        row_num = self.write_date_info(worksheet, workbook, row_num, col_count - 1, date, formats['right_align'])

        # 3. Header
        row_num = 2
        worksheet.set_row(row_num, 23)

        # 컬럼 너비 설정
        worksheet.set_column(0, 0, 12)  # 빈 열
        worksheet.set_column(1, 1, 15)  # 구분 열
        for i in range(len(pay_orders)):
            worksheet.set_column(2 + i, 2 + i, 15)  # 각 납부회차 열
        worksheet.set_column(col_count - 1, col_count - 1, 18)  # 계 열

        # Use header format from mixin
        h1format = formats['header']

        # Write main header
        worksheet.write(row_num, 0, '', h1format)  # 빈 열
        worksheet.write(row_num, 1, '구분', h1format)

        # 납부회차 헤더들
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['pay_name'], h1format)

        worksheet.write(row_num, col_count - 1, '합계', h1format)

        # 4. 약정일 행
        row_num = 3
        worksheet.set_row(row_num, 20)

        # Use default format from mixin
        due_date_format = formats['default']

        worksheet.write(row_num, 0, '기본', due_date_format)
        worksheet.write(row_num, 1, '약정일', due_date_format)

        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order.get('pay_due_date', ''), due_date_format)

        worksheet.write(row_num, col_count - 1, '', due_date_format)

        # 5. Body - 계약 섹션 (4행)
        # Use format objects from mixin
        body_format = formats['currency']
        center_format = formats['default']

        # 계약 섹션 - 계약
        row_num += 1
        contract_format = workbook.add_format({
            'bold': True,
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#eeeeee'
        })
        worksheet.merge_range(row_num, 0, row_num + 3, 0, '계약', contract_format)

        # 계약(세대수)
        worksheet.write(row_num, 1, f'계약({aggregate_data.get("conts_num", 0):,})', center_format)
        total_contract_amount = sum(order['contract_amount'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['contract_amount'], body_format)
        worksheet.write(row_num, col_count - 1, total_contract_amount, body_format)

        # 미계약(세대수)
        row_num += 1
        worksheet.write(row_num, 1, f'미계약({aggregate_data.get("non_conts_num", 0):,})',
                        center_format)
        total_non_contract_amount = sum(order['non_contract_amount'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['non_contract_amount'], body_format)
        worksheet.write(row_num, col_count - 1, total_non_contract_amount, body_format)

        # 총계(세대수)
        row_num += 1
        worksheet.write(row_num, 1, f'총계({aggregate_data.get("total_units", 0):,})', center_format)
        total_amount = total_contract_amount + total_non_contract_amount
        for i, order in enumerate(pay_orders):
            total_per_order = order['contract_amount'] + order['non_contract_amount']
            worksheet.write(row_num, 2 + i, total_per_order, body_format)
        worksheet.write(row_num, col_count - 1, total_amount, body_format)

        # 계약율 (금액 기준): 회차별 계약금액/약정금액, 합계는 총 계약금액/총매출액
        row_num += 1
        worksheet.write(row_num, 1, '계약율', center_format)

        # PaymentStatusByUnitTypeViewSet에서 금액 데이터 가져와서 총 계약률 계산
        payment_status_mock_request = Mock()
        payment_status_mock_request.query_params = {
            'project': str(project.pk),
            'date': date if date else 'null'
        }

        payment_status_viewset = PaymentStatusByUnitTypeViewSet()
        payment_status_response = payment_status_viewset.list(payment_status_mock_request)

        total_contract_rate = 0
        if payment_status_response.status_code == 200:
            payment_status_data = payment_status_response.data
            total_contract_amount = sum(item['contract_amount'] for item in payment_status_data)
            total_sales_amount = sum(item['total_sales_amount'] for item in payment_status_data)

            # 총 계약률 = 총 계약금액 / 총매출액 * 100
            total_contract_rate = (total_contract_amount / total_sales_amount * 100) if total_sales_amount > 0 else 0

        # Use percent format from mixin
        percent_format = formats['percent']

        # 회차별 계약률 계산 (Excel에서 직접 계산)
        for i, order in enumerate(pay_orders):
            # Excel에서 직접 계산 (API 데이터 문제로 인해 임시 직접 계산)
            order_total_amount = order['contract_amount'] + order['non_contract_amount']
            order_contract_rate = (order['contract_amount'] / order_total_amount * 100) if order_total_amount > 0 else 0
            worksheet.write(row_num, 2 + i, order_contract_rate / 100, percent_format)

        # 합계는 총 계약률 사용
        worksheet.write(row_num, col_count - 1, total_contract_rate / 100, percent_format)

        # 6. 수납 섹션 (5행)
        row_num += 1
        collection_format = workbook.add_format({
            'bold': True,
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#eeeeee'
        })
        worksheet.merge_range(row_num, 0, row_num + 4, 0, '수납', collection_format)

        # 수납액 - 표준화된 집계 방식 사용 (회차별, 합계 모두 표준화)
        worksheet.write(row_num, 1, '수납액', center_format)
        standardized_collected_amount = get_standardized_payment_sum(project, date)
        # 회차별로도 표준화된 계산 사용
        for i, order in enumerate(pay_orders):
            standardized_order_collected = get_standardized_payment_sum_by_order(project, date, order['pk'])
            worksheet.write(row_num, 2 + i, standardized_order_collected, body_format)
        worksheet.write(row_num, col_count - 1, standardized_collected_amount, body_format)

        # 할인료
        row_num += 1
        worksheet.write(row_num, 1, '할인료', center_format)
        total_discount_amount = sum(order['collection']['discount_amount'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['collection']['discount_amount'], body_format)
        worksheet.write(row_num, col_count - 1, total_discount_amount, body_format)

        # 연체료
        row_num += 1
        worksheet.write(row_num, 1, '연체료', center_format)
        total_overdue_fee = sum(order['collection']['overdue_fee'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['collection']['overdue_fee'], body_format)
        worksheet.write(row_num, col_count - 1, total_overdue_fee, body_format)

        # 실수납액 - 표준화된 집계 방식 사용 (회차별, 합계 모두 표준화)
        row_num += 1
        worksheet.write(row_num, 1, '실수납액', center_format)
        standardized_actual_collected = get_standardized_payment_sum(project, date)
        # 회차별로도 표준화된 계산 사용 (할인료, 연체료 미구현으로 수납액과 동일)
        for i, order in enumerate(pay_orders):
            standardized_order_actual = get_standardized_payment_sum_by_order(project, date, order['pk'])
            worksheet.write(row_num, 2 + i, standardized_order_actual, body_format)
        worksheet.write(row_num, col_count - 1, standardized_actual_collected, body_format)

        # 수납율 - 표준화된 집계 기반으로 계산 (회차별, 합계 모두 표준화)
        row_num += 1
        worksheet.write(row_num, 1, '수납율', center_format)
        total_collection_rate = (
                standardized_actual_collected / total_contract_amount * 100) if total_contract_amount > 0 else 0
        # 회차별 수납율도 표준화된 계산으로 수정
        for i, order in enumerate(pay_orders):
            standardized_order_actual = get_standardized_payment_sum_by_order(project, date, order['pk'])
            order_contract_amount = order['contract_amount']
            order_collection_rate = (
                    standardized_order_actual / order_contract_amount * 100) if order_contract_amount > 0 else 0
            worksheet.write(row_num, 2 + i, order_collection_rate / 100, percent_format)
        worksheet.write(row_num, col_count - 1, total_collection_rate / 100, percent_format)

        # 7. 기간도래 섹션 (5행)
        row_num += 1
        due_period_format = workbook.add_format({
            'bold': True,
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#eeeeee'
        })
        worksheet.merge_range(row_num, 0, row_num + 4, 0, '기간도래', due_period_format)

        # 약정금액
        worksheet.write(row_num, 1, '약정금액', center_format)
        total_due_contract_amount = sum(order['due_period']['contract_amount'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['due_period']['contract_amount'], body_format)
        worksheet.write(row_num, col_count - 1, total_due_contract_amount, body_format)

        # 미수금
        row_num += 1
        worksheet.write(row_num, 1, '미수금', center_format)
        total_due_unpaid_amount = sum(order['due_period']['unpaid_amount'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['due_period']['unpaid_amount'], body_format)
        worksheet.write(row_num, col_count - 1, total_due_unpaid_amount, body_format)

        # 미수율
        row_num += 1
        worksheet.write(row_num, 1, '미수율', center_format)
        total_due_unpaid_rate = (
                total_due_unpaid_amount / total_due_contract_amount * 100) if total_due_contract_amount > 0 else 0
        for i, order in enumerate(pay_orders):
            unpaid_rate = float(order['due_period']['unpaid_rate'])
            worksheet.write(row_num, 2 + i, unpaid_rate / 100, percent_format)
        worksheet.write(row_num, col_count - 1, total_due_unpaid_rate / 100, percent_format)

        # 연체료
        row_num += 1
        worksheet.write(row_num, 1, '연체료', center_format)
        total_due_overdue_fee = sum(order['due_period']['overdue_fee'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['due_period']['overdue_fee'], body_format)
        worksheet.write(row_num, col_count - 1, total_due_overdue_fee, body_format)

        # 소계
        row_num += 1
        worksheet.write(row_num, 1, '소계', center_format)
        total_due_subtotal = sum(order['due_period']['subtotal'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['due_period']['subtotal'], body_format)
        worksheet.write(row_num, col_count - 1, total_due_subtotal, body_format)

        # 8. 기간미도래 섹션 (1행)
        row_num += 1
        not_due_format = workbook.add_format({
            'bold': True,
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#eeeeee'
        })
        worksheet.write(row_num, 0, '기간미도래', not_due_format)
        worksheet.write(row_num, 1, '미수금', center_format)
        total_not_due_unpaid = sum(order['not_due_unpaid'] for order in pay_orders)
        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['not_due_unpaid'], body_format)
        worksheet.write(row_num, col_count - 1, total_not_due_unpaid, body_format)

        # 9. 총계 섹션 (2행)
        row_num += 1
        total_format = workbook.add_format({
            'bold': True,
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#eeeeee'
        })
        worksheet.merge_range(row_num, 0, row_num + 1, 0, '총계', total_format)

        # 미수금 (기간도래 누적 + 기간미도래 전체)
        worksheet.write(row_num, 1, '미수금', center_format)

        # 전체 미수금 찾기 (마지막 기간도래 회차에서)
        total_overall_unpaid = sum(order['total_unpaid'] for order in pay_orders)  # 기본값
        for order in reversed(pay_orders):  # 뒤에서부터 찾기
            if 'total_overall_unpaid' in order:
                total_overall_unpaid = order['total_overall_unpaid']
                break

        for i, order in enumerate(pay_orders):
            worksheet.write(row_num, 2 + i, order['total_unpaid'], body_format)
        worksheet.write(row_num, col_count - 1, total_overall_unpaid, body_format)

        # 미수율 (전체 미수금 기준)
        row_num += 1
        worksheet.write(row_num, 1, '미수율', center_format)

        # 전체 미수율 계산 (총 미수금 / 총 계약금액)
        total_overall_unpaid_rate = (
                total_overall_unpaid / total_contract_amount * 100) if total_contract_amount > 0 else 0

        for i, order in enumerate(pay_orders):
            total_unpaid_rate = float(order['total_unpaid_rate'])
            worksheet.write(row_num, 2 + i, total_unpaid_rate / 100, percent_format)
        worksheet.write(row_num, col_count - 1, total_overall_unpaid_rate / 100, percent_format)

        # Create a response using mixin
        filename = request.GET.get('filename', 'overall-summary')
        filename = f'{filename}-{date}'
        return self.create_response(output, workbook, filename)
