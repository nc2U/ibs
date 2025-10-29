"""
Contract Excel Export Views

계약 관련 Excel 내보내기 뷰들
"""
import datetime
import io

import xlsxwriter
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, Max, OuterRef, Subquery
from django.http import HttpResponse

from _excel.mixins import ExcelExportMixin
from cash.models import ProjectCashBook
from contract.models import Contract, Succession, ContractorRelease
from contract.models import ContractorAddress
from items.models import HouseUnit, BuildingUnit
from project.models import Project

TODAY = datetime.date.today().strftime('%Y-%m-%d')


class ExportContracts(ExcelExportMixin):
    """계약자 리스트"""

    def get(self, request):
        # 워크북 생성
        t_name = '계약' if request.GET.get('status') == '2' else '청약'
        output, workbook, worksheet = self.create_workbook(f'{t_name}목록_정보')

        project = Project.objects.get(pk=request.GET.get('project'))
        cols = sorted(list(map(int, request.GET.get('col').split('-'))))

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)
        body_format = {
            'border': True,
            'valign': 'vcenter',
            'num_format': '#,##0',
            'align': 'center',
        }

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.merge_range(row_num, 0, row_num, len(cols), str(project) + f' {t_name}자 리스트', title_format)

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(cols), TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header
        row_num = 2
        worksheet.set_row(row_num, 23, workbook.add_format({'bold': True}))

        # title_list
        header_src = [[],
                      ['일련번호', 'serial_number', 10],
                      ['등록상태', 'contractor__qualification', 8],
                      ['차수', 'order_group__name', 10],
                      ['타입', 'key_unit__unit_type__name', 7],
                      [f'{t_name}자', 'contractor__name', 10],
                      ['동', 'key_unit__houseunit__building_unit__name', 7],
                      ['호수', 'key_unit__houseunit__name', 7],
                      [f'가입{t_name}일', 'contractor__contract_date', 12],
                      [f'공급계약일', 'sup_cont_date', 12],
                      ['건물가', 'contractor__contract__contractprice__price_build', 12],
                      ['대지가', 'contractor__contract__contractprice__price_land', 12],
                      ['부가세', 'contractor__contract__contractprice__price_tax', 11],
                      ['공급가액', 'contractor__contract__contractprice__price', 12],
                      ['납입금합계', '', 12],
                      ['생년월일', 'contractor__birth_date', 12],
                      ['연락처[1]', 'contractor__contractorcontact__cell_phone', 14],
                      ['연락처[2]', 'contractor__contractorcontact__home_phone', 14],
                      ['연락처[3]', 'contractor__contractorcontact__other_phone', 14],
                      ['이메일', 'contractor__contractorcontact__email', 15],
                      ['주소[등본]', 'contractor__addresses__id_zipcode', 7],
                      ['', 'contractor__addresses__id_address1', 35],
                      ['', 'contractor__addresses__id_address2', 20],
                      ['', 'contractor__addresses__id_address3', 40],
                      ['주소[우편]', 'contractor__addresses__dm_zipcode', 7],
                      ['', 'contractor__addresses__dm_address1', 35],
                      ['', 'contractor__addresses__dm_address2', 20],
                      ['', 'contractor__addresses__dm_address3', 40],
                      ['비고', 'contractor__note', 45]]

        titles = ['No']
        params = ['pk']
        widths = [7]

        for n in cols:  # 요청된 컬럼 개수 만큼 반복 (1-2-3... -> i)
            titles.append(header_src[n][0])  # 일련번호
            params.append(header_src[n][1])  # serial_number
            widths.append(header_src[n][2])  # 10

        while '' in params:
            params.remove('')

        # Adjust the column width.
        for i, cw in enumerate(widths):  # 각 컬럼 넙이 세팅
            worksheet.set_column(i, i, cw)

        # Write header
        for col_num, col in enumerate(titles):  # 헤더 줄 제목 세팅
            if '주소' in col:
                worksheet.merge_range(row_num, col_num, row_num, col_num + 3, titles[col_num], h_format)
            else:
                worksheet.write(row_num, col_num, titles[col_num], h_format)

        # 4. Body

        # Turn off some warnings:
        worksheet.ignore_errors({'number_stored_as_text': 'B:Y'})

        # ----------------- get_queryset start ----------------- #
        # Get some data to write to the spreadsheet.
        # Use select_related to optimize and ensure we get the current address
        queryset = Contract.objects.filter(project=project,
                                           activation=True,
                                           contractor__status='2').select_related(
            'contractor'
        ).prefetch_related(
            'contractor__addresses'
        ).order_by('contractor__contract_date')
        status = request.GET.get('status')
        group = request.GET.get('group')
        type = request.GET.get('type')
        dong = request.GET.get('dong')
        is_null = request.GET.get('is_null')
        quali = request.GET.get('quali')
        sup = request.GET.get('sup')
        sdate = request.GET.get('sdate')
        edate = request.GET.get('edate')
        q = request.GET.get('q')

        queryset = queryset.filter(contractor__status=status) if status else queryset
        queryset = queryset.filter(order_group=group) if group else queryset
        queryset = queryset.filter(unit_type=type) if type else queryset
        queryset = queryset.filter(key_unit__houseunit__building_unit=dong) if dong else queryset
        null_qry = True if is_null == '1' else False
        queryset = queryset.filter(key_unit__houseunit__isnull=null_qry) if is_null else queryset
        queryset = queryset.filter(contractor__qualification=quali) if quali else queryset
        sup_qry = True if sup == 'true' else False
        queryset = queryset.filter(is_sup_cont=sup_qry) if sup else queryset
        queryset = queryset.filter(contractor__contract_date__gte=sdate) if sdate else queryset
        queryset = queryset.filter(contractor__contract_date__lte=edate) if edate else queryset
        queryset = queryset.filter(
            Q(serial_number__icontains=q) |
            Q(contractor__name__icontains=q) |
            Q(contractor__note__icontains=q) |
            Q(contractor__contractorcontact__cell_phone__icontains=q)) if q else queryset

        order_qry = request.GET.get('order')
        order_list = ['-created', 'created', '-contractor__contract_date',
                      'contractor__contract_date', '-serial_number',
                      'serial_number', '-contractor__name', 'contractor__name']
        queryset = queryset.order_by(order_list[int(order_qry)]) if order_qry else queryset

        # ----------------- get_queryset finish ----------------- #
        # Use annotations to get current address fields

        # Annotate with current address fields using Subquery
        current_address_subquery = ContractorAddress.objects.filter(
            contractor=OuterRef('contractor'),
            is_current=True
        )

        queryset = queryset.annotate(
            current_id_zipcode=Subquery(current_address_subquery.values('id_zipcode')[:1]),
            current_id_address1=Subquery(current_address_subquery.values('id_address1')[:1]),
            current_id_address2=Subquery(current_address_subquery.values('id_address2')[:1]),
            current_id_address3=Subquery(current_address_subquery.values('id_address3')[:1]),
            current_dm_zipcode=Subquery(current_address_subquery.values('dm_zipcode')[:1]),
            current_dm_address1=Subquery(current_address_subquery.values('dm_address1')[:1]),
            current_dm_address2=Subquery(current_address_subquery.values('dm_address2')[:1]),
            current_dm_address3=Subquery(current_address_subquery.values('dm_address3')[:1]),
        )

        # Replace address field references with annotated fields
        updated_params = []
        for param in params:
            if param == 'contractor__addresses__id_zipcode':
                updated_params.append('current_id_zipcode')
            elif param == 'contractor__addresses__id_address1':
                updated_params.append('current_id_address1')
            elif param == 'contractor__addresses__id_address2':
                updated_params.append('current_id_address2')
            elif param == 'contractor__addresses__id_address3':
                updated_params.append('current_id_address3')
            elif param == 'contractor__addresses__dm_zipcode':
                updated_params.append('current_dm_zipcode')
            elif param == 'contractor__addresses__dm_address1':
                updated_params.append('current_dm_address1')
            elif param == 'contractor__addresses__dm_address2':
                updated_params.append('current_dm_address2')
            elif param == 'contractor__addresses__dm_address3':
                updated_params.append('current_dm_address3')
            else:
                updated_params.append(param)

        data = queryset.values_list(*updated_params)

        is_date = []  # ('생년월일', '계약일자')
        is_left = []  # ('주소', '비고')
        is_num = []  # ('공급가액', '납입금합계', '회당계약금', '회당중도금', '회장잔금')
        reg_col = None  # ('등록상태',)
        sum_col = None  # 납입금합계 컬럼 위치

        # Write body
        for col_num, title in enumerate(titles):
            if title in ('생년월일', f'{t_name}일자'):
                is_date.append(col_num)
            if title == '등록상태':
                reg_col = col_num
            if title in ('건물가', '대지가', '부가세', '공급가액', '납입금합계', '회당계약금', '회당중도금', '회당잔금'):
                is_num.append(col_num)
                if title == '납입금합계':
                    sum_col = col_num
            if title in ('', '비고'):
                is_left.append(col_num)

        paid_params = ['contract', 'income']
        paid_data = ProjectCashBook.objects.filter(project_account_d3__is_payment=True,
                                                   income__isnull=False,
                                                   contract__activation=True)
        paid_dict = paid_data.values_list(*paid_params)

        quali_str = {'1': '일반분양', '2': '미인가', '3': '인가', '4': '부적격', }

        for i, row in enumerate(data):
            row_num += 1
            row = list(row)

            if sum_col is not None:
                paid_sum = sum([ps[1] for ps in paid_dict if ps[0] == row[0]])
                row.insert(sum_col, paid_sum)  # 순서 삽입

            row[0] = i + 1  # pk 대신 순서 삽입

            for col_num, cell_data in enumerate(row):
                # css 설정
                if col_num == 0:
                    body_format['align'] = 'center'
                    body_format['num_format'] = '#,##0'
                elif col_num in is_num:
                    body_format['num_format'] = 41
                elif col_num in is_left:
                    body_format['align'] = 'left'
                else:
                    body_format['align'] = 'center'
                    body_format['num_format'] = 'yyyy-mm-dd'

                # 인가 여부 데이터 치환
                cell_value = quali_str.get(cell_data, '') if reg_col == col_num else cell_data
                bf = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_value, bf)

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = request.GET.get('filename') or 'contracts'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportApplicants(ExcelExportMixin):
    """청약자 리스트"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('청약목록_정보')

        project = Project.objects.get(pk=request.GET.get('project'))

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)
        body_format = {
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': 'yyyy-mm-dd'
        }

        # title_list
        header_src = [[],
                      ['일련번호', 'serial_number', 10],
                      ['차수', 'order_group__name', 10],
                      ['타입', 'key_unit__unit_type__name', 7],
                      ['청약자', 'contractor__name', 10],
                      ['청약일자', 'contractor__reservation_date', 12],
                      ['연락처[1]', 'contractor__contractorcontact__cell_phone', 14],
                      ['연락처[2]', 'contractor__contractorcontact__home_phone', 14],
                      ['연락처[3]', 'contractor__contractorcontact__other_phone', 14],
                      ['이메일', 'contractor__contractorcontact__email', 15],
                      ['비고', 'contractor__note', 45]]

        if project.is_unit_set:
            header_src.append(
                ['동', 'key_unit__houseunit__building_unit', 7],
                ['호수', 'key_unit__houseunit__name', 7]
            )

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, str(project) + ' 청약자 리스트', title_format)

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header
        row_num = 2
        worksheet.set_row(row_num, 25, workbook.add_format({'bold': True}))

        titles = ['No']  # header titles
        params = []  # ORM 추출 field
        widths = [7]  # No. 컬럼 넓이

        for ds in header_src:
            if ds:
                titles.append(ds[0])
                params.append(ds[1])
                widths.append(ds[2])

        # Adjust the column width.
        for i, col_width in enumerate(widths):
            worksheet.set_column(i, i, col_width)

        # Write header
        for col_num, col in enumerate(titles):
            worksheet.write(row_num, col_num, titles[col_num], h_format)

        # 4. Body
        # Get some data to write to the spreadsheet.
        data = Contract.objects.filter(project=project,
                                       contractor__status='1')

        data = data.values_list(*params)

        is_left = []
        # Write header
        for col_num, col in enumerate(titles):
            if col in ('비고'):
                is_left.append(col_num)

        # Write header
        for i, row in enumerate(data):
            row = list(row)
            row_num += 1
            row.insert(0, i + 1)
            for col_num, cell_data in enumerate(row):
                if col_num == 0:
                    body_format['num_format'] = '#,##0'
                else:
                    body_format['num_format'] = 'yyyy-mm-dd'
                if col_num in is_left:
                    if 'align' in body_format:
                        del body_format['align']
                else:
                    if 'align' not in body_format:
                        body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = request.GET.get('filename') or 'applicants'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportSuccessions(ExcelExportMixin):
    """권리의무승계 리스트"""

    @staticmethod
    def get(request):

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('권리의무승계_목록')

        worksheet.set_default_row(20)

        project = Project.objects.get(pk=request.GET.get('project'))

        # title_list
        header_src = [[],
                      ['계약 정보', 'contract', 15],
                      ['양도계약자', 'seller', 13],
                      ['양수계약자', 'buyer', 13],
                      ['승계신청일', 'apply_date', 15],
                      ['매매계약일', 'trading_date', 15],
                      ['변경인가일', 'approval_date', 15],
                      ['변경인가여부', 'is_approval', 13],
                      ['비고', 'note', 45]]

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)
        title_format = workbook.add_format()
        title_format.set_bold()
        title_format.set_font_size(18)
        title_format.set_align('vcenter')
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, str(project) + ' 권리의무승계 목록', title_format)

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header - 1
        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

        titles = ['No']  # header titles
        params = []  # ORM 추출 field
        widths = [7]  # No. 컬럼 넓이

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

        # Write header - 1
        for col_num, title in enumerate(titles):
            worksheet.write(row_num, col_num, title, h_format)

        # 4. Body
        # Get some data to write to the spreadsheet.
        obj_list = Succession.objects.filter(contract__project=project)

        data = obj_list.values_list(*params)

        b_format = workbook.add_format()
        b_format.set_border()
        b_format.set_align('center')
        b_format.set_align('vcenter')
        b_format.set_num_format('yyyy-mm-dd')

        body_format = {
            'border': True,
            'valign': 'vcenter',
            'num_format': 'yyyy-mm-dd'
        }

        # Turn off some of the warnings:
        worksheet.ignore_errors({'number_stored_as_text': 'F:G'})

        # Write header
        for i, row in enumerate(data):
            row = list(row)
            row_num += 1
            row.insert(0, i + 1)
            for col_num, cell_data in enumerate(row):
                if col_num == 1:
                    cell_data = obj_list.get(contract=cell_data).contract.__str__()
                if col_num == 2:
                    cell_data = obj_list.get(seller=cell_data).contract.contractor.name
                if col_num == 3:
                    cell_data = obj_list.get(buyer=cell_data).buyer.name
                if col_num not in (4, 5, 6):
                    body_format['num_format'] = '#,##0'
                else:
                    body_format['num_format'] = 'yyyy-mm-dd'
                if col_num == 7:
                    cell_data = '완료' if cell_data else ''
                if col_num == 8:
                    body_format['align'] = 'left'
                else:
                    body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = '{date}-successions.xlsx'.format(date=TODAY)
        file_format = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = HttpResponse(output, content_type=file_format)
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response


class ExportReleases(ExcelExportMixin):
    """해지자 리스트"""

    @staticmethod
    def get(request):

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('해지자목록_정보')

        worksheet.set_default_row(20)

        project = Project.objects.get(pk=request.GET.get('project'))

        # title_list
        header_src = [[],
                      ['해지자', 'contractor__name', 10],
                      ['해지일련번호', 'contractor__contract__serial_number', 30],
                      ['현재상태', 'status', 12],
                      ['환불(예정)금액', 'refund_amount', 15],
                      ['은행', 'refund_account_bank', 15],
                      ['계좌번호', 'refund_account_number', 18],
                      ['예금주', 'refund_account_depositor', 12],
                      ['해지신청일', 'request_date', 14],
                      ['환불처리일', 'completion_date', 14],
                      ['비고', 'note', 45]]

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)
        title_format = workbook.add_format()
        title_format.set_bold()
        title_format.set_font_size(18)
        title_format.set_align('vcenter')
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, str(project) + ' 해지자 리스트', title_format)

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header - 1
        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

        titles = ['No']  # header titles
        params = []  # ORM 추출 field
        widths = [7]  # No. 컬럼 넓이

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

        # Write header - 1
        for col_num, title in enumerate(titles):
            if col_num == 5:
                worksheet.merge_range(row_num, col_num, row_num, col_num + 2, '환불 계좌', h_format)
            elif col_num in [6, 7]:
                pass
            else:
                worksheet.write(row_num, col_num, title, h_format)

        # Write Header - 2
        row_num = 3
        for col_num, title in enumerate(titles):
            if col_num in [5, 6, 7]:
                worksheet.write(row_num, col_num, title, h_format)
            else:
                worksheet.merge_range(row_num - 1, col_num, row_num, col_num, title, h_format)

        # 4. Body
        # Get some data to write to the spreadsheet.
        queryset = ContractorRelease.objects.filter(project=project)

        data = queryset.values_list(*params)

        b_format = workbook.add_format()
        b_format.set_border()
        b_format.set_align('center')
        b_format.set_align('vcenter')
        b_format.set_num_format('yyyy-mm-dd')

        body_format = {
            'border': True,
            'valign': 'vcenter',
            'num_format': 'yyyy-mm-dd'
        }

        # Turn off some of the warnings:
        worksheet.ignore_errors({'number_stored_as_text': 'F:G'})

        # Write header
        choice = dict(ContractorRelease.STATUS_CHOICES)
        for i, row in enumerate(data):
            row = list(row)
            row_num += 1
            row.insert(0, i + 1)
            for col_num, cell_data in enumerate(row):
                if col_num == 0:
                    body_format['num_format'] = '#,##0'
                else:
                    body_format['num_format'] = 'yyyy-mm-dd'
                if col_num == 4:
                    body_format['num_format'] = 41
                elif col_num == 10:
                    body_format['align'] = 'left'
                else:
                    body_format['align'] = 'center'
                if col_num == 3:
                    cell_data = choice[cell_data]
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = '{date}-releases.xlsx'.format(date=TODAY)
        file_format = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = HttpResponse(output, content_type=file_format)
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response


class ExportUnitStatus(ExcelExportMixin):
    """동호수 현황표"""

    @staticmethod
    def get(request):
        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('동호수현황표')

        worksheet.set_default_row(15)

        # data start --------------------------------------------- #
        project = Project.objects.get(pk=request.GET.get('project'))
        max_floor = HouseUnit.objects.aggregate(Max('floor_no'))
        floor_no__max = max_floor['floor_no__max'] if max_floor['floor_no__max'] else 1
        max_floor_range = range(0, floor_no__max)
        unit_numbers = HouseUnit.objects.filter(building_unit__project=project)
        dong_obj = BuildingUnit.objects.filter(project=project).values('name')
        is_contor = True if request.GET.get('iscontor') == 'true' else False

        # 1. Title
        row_num = 0
        title_format = workbook.add_format()
        worksheet.set_row(row_num, 50)
        title_format.set_font_size(18)
        title_format.set_align('vcenter')
        title_format.set_bold()

        worksheet.write(row_num, 0, str(project) + ' 동호수 현황표', title_format)

        # 2. Sub Description
        max_col = 0
        row_num = 1

        for dong in dong_obj:
            lines = unit_numbers.order_by('bldg_line').values('bldg_line').filter(
                building_unit__name__contains=dong['name']).distinct()
            for line in lines:
                max_col += 1
            max_col += 1

        worksheet.write(row_num, max_col, TODAY + ' 현재', workbook.add_format({'align': 'right', 'font_size': '9'}))

        # 3. Unit status board
        row_num = 3
        worksheet.set_column(0, max_col, 5.5)
        unit_format = {
            'border': True,
            'font_size': 8,
            'align': 'center',
            'valign': 'vcenter'
        }
        status_format = {
            'border': True,
            'font_size': 8,
            'align': 'center',
            'valign': 'vcenter'
        }
        # 최고층수 만큼 반복
        for mf in max_floor_range:
            row_num += 2
            floor_no = floor_no__max - mf  # 현재 층수
            col_num = 1
            # 동 수 만큼 반복
            for dong in dong_obj:  # 동호수 표시 라인
                units = unit_numbers.filter(building_unit__name=dong['name'])
                lines = unit_numbers.order_by('bldg_line').values('bldg_line').filter(
                    building_unit__name__contains=dong['name']).distinct()
                for line in lines:
                    try:
                        unit = units.get(floor_no=floor_no, bldg_line=line['bldg_line'])
                    except ObjectDoesNotExist:
                        unit = None
                    if unit or floor_no <= 2:
                        unit_format['bg_color'] = unit.unit_type.color if unit else '#BBBBBB'
                        unit_formats = workbook.add_format(unit_format)
                        if not unit:
                            worksheet.merge_range(row_num, col_num, row_num + 1, col_num, '', unit_formats)
                        else:
                            worksheet.write(row_num, col_num, int(unit.name), unit_formats)
                            if unit.key_unit:
                                if int(unit.key_unit.contract.contractor.status) % 2 == 0:
                                    status_format['bg_color'] = '#DDDDDD'
                                    status_format['font_color'] = 'black'
                                else:
                                    status_format['bg_color'] = '#FFFF99'
                                    status_format['font_color'] = 'black'
                            elif unit.is_hold:
                                status_format['bg_color'] = '#999999'
                                status_format['font_color'] = 'black'
                            else:
                                status_format['bg_color'] = 'white'
                            cont = unit.key_unit.contract.contractor.name if unit.key_unit and is_contor else ''
                            status_formats = workbook.add_format(status_format)
                            worksheet.write(row_num + 1, col_num, cont, status_formats)
                    col_num += 1
                col_num += 1

        row_num += 2
        col_num = 1

        dong_title_format = workbook.add_format()
        dong_title_format.set_bold()
        dong_title_format.set_border()
        dong_title_format.set_font_size(11)
        dong_title_format.set_align('center')
        dong_title_format.set_align('vcenter')
        dong_title_format.set_bg_color('#777777')
        dong_title_format.set_font_color('#FFFFFF')

        # 동 수 만큼 반복
        for dong in dong_obj:  # 호수 상태 표시 라인
            lines = unit_numbers.order_by('-bldg_line').values('bldg_line').filter(
                building_unit__name__contains=dong['name']).distinct()
            worksheet.merge_range(row_num, col_num, row_num + 1, col_num + lines.count() - 1,
                                  dong['name'] + '동',
                                  dong_title_format)

            col_num = col_num + lines.count() + 1

        # data end ----------------------------------------------- #

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = '{date}-unit-status-board.xlsx'.format(date=TODAY)
        file_format = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = HttpResponse(output, content_type=file_format)
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response
