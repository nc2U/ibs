"""
Contract Excel Export Views

계약 관련 Excel 내보내기 뷰들
"""
import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, Max

from _excel.mixins import ExcelExportMixin, ProjectFilterMixin, ExcelUtilsMixin
from _excel.utils import create_filename, filter_headers_by_columns
from cash.models import ProjectCashBook
from contract.models import Contract, Succession, ContractorRelease
from items.models import HouseUnit, BuildingUnit

TODAY = datetime.date.today().strftime('%Y-%m-%d')


class ExportContracts(ExcelExportMixin, ProjectFilterMixin, ExcelUtilsMixin):
    """계약자 리스트 Excel 내보내기"""

    def get(self, request):
        project = self.get_project(request)
        cols = self.get_selected_columns(request)
        status = request.GET.get('status', '2')
        t_name = '계약' if status == '2' else '청약'

        # Excel 워크북 생성
        output, workbook, worksheet = self.create_workbook(f'{t_name}목록_정보')

        # 헤더 정의
        header_src = self._get_contract_headers(t_name)
        filtered_headers = filter_headers_by_columns(header_src, cols) if cols else header_src

        # 제목 및 헤더 작성
        row_num = self.write_title(worksheet, workbook, 0, len(filtered_headers) - 1,
                                   f'{project} {t_name}자 리스트')
        row_num = self.write_date_info(worksheet, workbook, row_num, len(filtered_headers) - 1)
        row_num = self._write_contract_headers(worksheet, workbook, row_num, filtered_headers)

        # 데이터 조회 및 작성
        queryset = self._get_contract_queryset(request, project)
        self._write_contract_data(worksheet, workbook, row_num, filtered_headers, queryset)

        # 응답 생성
        filename = create_filename('contracts', project.name, t_name)
        return self.create_response(output, workbook, filename)

    def _get_contract_headers(self, t_name):
        """계약 헤더 정의"""
        return [
            [],
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
            ['주소[등본]', 'contractor__contractoraddress__id_zipcode', 7],
            ['', 'contractor__contractoraddress__id_address1', 35],
            ['', 'contractor__contractoraddress__id_address2', 20],
            ['', 'contractor__contractoraddress__id_address3', 40],
            ['주소[우편]', 'contractor__contractoraddress__dm_zipcode', 7],
            ['', 'contractor__contractoraddress__dm_address1', 35],
            ['', 'contractor__contractoraddress__dm_address2', 20],
            ['', 'contractor__contractoraddress__dm_address3', 40],
            ['비고', 'contractor__note', 45]
        ]

    def _write_contract_headers(self, worksheet, workbook, row_num, headers):
        """계약 헤더 작성 (주소 병합 처리)"""
        h_format = self.create_header_format(workbook)
        worksheet.set_row(row_num, 23, workbook.add_format({'bold': True}))

        titles = ['No']
        widths = [7]

        for header in headers[1:]:  # 첫 번째 빈 헤더 제외
            if header:
                titles.append(header[0])
                widths.append(header[2])

        # 컬럼 너비 설정
        for i, width in enumerate(widths):
            worksheet.set_column(i, i, width)

        # 헤더 작성 (주소 병합 처리)
        for col_num, title in enumerate(titles):
            if '주소' in title:
                worksheet.merge_range(row_num, col_num, row_num, col_num + 3, title, h_format)
            else:
                worksheet.write(row_num, col_num, title, h_format)

        return row_num + 1

    def _get_contract_queryset(self, request, project):
        """계약 쿼리셋 생성"""
        queryset = Contract.objects.filter(
            project=project,
            activation=True,
            contractor__status='2'
        ).order_by('contractor__contract_date')

        # 필터 적용
        filters = self._extract_filters(request)
        for filter_key, filter_value in filters.items():
            if filter_value is not None:
                queryset = queryset.filter(**{filter_key: filter_value})

        # 검색 쿼리 적용
        q = request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(serial_number__icontains=q) |
                Q(contractor__name__icontains=q) |
                Q(contractor__note__icontains=q) |
                Q(contractor__contractorcontact__cell_phone__icontains=q)
            )

        # 정렬 적용
        order = request.GET.get('order')
        if order:
            order_list = ['-created', 'created', '-contractor__contract_date',
                          'contractor__contract_date', '-serial_number',
                          'serial_number', '-contractor__name', 'contractor__name']
            if int(order) < len(order_list):
                queryset = queryset.order_by(order_list[int(order)])

        return queryset

    def _extract_filters(self, request):
        """요청에서 필터 추출"""
        filters = {}

        status = request.GET.get('status')
        if status:
            filters['contractor__status'] = status

        group = request.GET.get('group')
        if group:
            filters['order_group'] = group

        type_param = request.GET.get('type')
        if type_param:
            filters['unit_type'] = type_param

        dong = request.GET.get('dong')
        if dong:
            filters['key_unit__houseunit__building_unit'] = dong

        is_null = request.GET.get('is_null')
        if is_null:
            filters['key_unit__houseunit__isnull'] = is_null == '1'

        quali = request.GET.get('quali')
        if quali:
            filters['contractor__qualification'] = quali

        sup = request.GET.get('sup')
        if sup:
            filters['is_sup_cont'] = sup == 'true'

        sdate = request.GET.get('sdate')
        if sdate:
            filters['contractor__contract_date__gte'] = sdate

        edate = request.GET.get('edate')
        if edate:
            filters['contractor__contract_date__lte'] = edate

        return filters

    def _write_contract_data(self, worksheet, workbook, row_num, headers, queryset):
        """계약 데이터 작성"""
        # 필드 추출
        params = ['pk']
        for header in headers[1:]:
            if header and header[1]:
                params.append(header[1])

        # 납부금 데이터 미리 조회
        paid_data = ProjectCashBook.objects.filter(
            project_account_d3__is_payment=True,
            income__isnull=False,
            contract__activation=True
        ).values_list('contract', 'income')

        paid_dict = {}
        for contract_id, income in paid_data:
            if contract_id not in paid_dict:
                paid_dict[contract_id] = 0
            paid_dict[contract_id] += income

        # 자격 변환 딕셔너리
        quali_str = {'1': '일반분양', '2': '미인가', '3': '인가', '4': '부적격'}

        # 데이터 작성
        data = queryset.values_list(*params)

        for i, row in enumerate(data):
            row = list(row)
            row[0] = i + 1  # 순번으로 변경

            # 납입금합계 추가
            if any('납입금합계' in str(h[0]) for h in headers if h):
                paid_sum = paid_dict.get(queryset[i].pk, 0)
                # 납입금합계 컬럼 위치 찾기
                sum_col_idx = next((idx for idx, h in enumerate(headers) if h and '납입금합계' in h[0]), None)
                if sum_col_idx:
                    row.insert(sum_col_idx - 1, paid_sum)  # 헤더 인덱스 보정

            for col_num, cell_data in enumerate(row):
                # 자격 상태 변환
                if col_num < len(headers) and headers[col_num] and '등록상태' in str(headers[col_num][0]):
                    cell_data = quali_str.get(str(cell_data), cell_data)

                # 포맷 설정
                cell_format = self._get_cell_format(workbook, col_num, headers)
                worksheet.write(row_num, col_num, cell_data, cell_format)

            row_num += 1

    def _get_cell_format(self, workbook, col_num, headers):
        """셀 포맷 생성"""
        body_format = {
            'border': True,
            'valign': 'vcenter',
            'align': 'center',
        }

        if col_num == 0:
            body_format['num_format'] = '#,##0'
        elif col_num < len(headers) and headers[col_num]:
            header_name = headers[col_num][0] if headers[col_num] else ''
            if any(keyword in header_name for keyword in ['건물가', '대지가', '부가세', '공급가액', '납입금합계']):
                body_format['num_format'] = 41  # 통화 형식
            elif any(keyword in header_name for keyword in ['주소', '비고']):
                body_format['align'] = 'left'
            elif any(keyword in header_name for keyword in ['생년월일', '일자']):
                body_format['num_format'] = 'yyyy-mm-dd'

        return workbook.add_format(body_format)


class ExportApplicants(ExcelExportMixin, ProjectFilterMixin):
    """청약자 리스트 Excel 내보내기"""

    def get(self, request):
        project = self.get_project(request)

        # Excel 워크북 생성
        output, workbook, worksheet = self.create_workbook('청약목록_정보')

        # 헤더 정의
        headers = self._get_applicant_headers(project)

        # 제목 및 헤더 작성
        row_num = self.write_title(worksheet, workbook, 0, len(headers) - 1,
                                   f'{project} 청약자 리스트')
        row_num = self.write_date_info(worksheet, workbook, row_num, len(headers) - 1)
        row_num = self.write_headers(worksheet, workbook, row_num, headers)

        # 데이터 조회 및 작성
        queryset = self._get_applicant_queryset(request, project)
        self._write_applicant_data(worksheet, workbook, row_num, headers, queryset)

        # 응답 생성
        filename = create_filename('applicants', project.name)
        return self.create_response(output, workbook, filename)

    def _get_applicant_headers(self, project):
        """청약자 헤더 정의"""
        headers = [
            [],
            ['일련번호', 'serial_number', 10],
            ['차수', 'order_group__name', 10],
            ['타입', 'key_unit__unit_type__name', 7],
            ['청약자', 'contractor__name', 10],
            ['청약일자', 'contractor__reservation_date', 12],
            ['연락처[1]', 'contractor__contractorcontact__cell_phone', 14],
            ['연락처[2]', 'contractor__contractorcontact__home_phone', 14],
            ['연락처[3]', 'contractor__contractorcontact__other_phone', 14],
            ['이메일', 'contractor__contractorcontact__email', 15],
            ['비고', 'contractor__note', 45]
        ]

        # 동호수 설정이 있는 경우 추가
        if project.is_unit_set:
            headers.extend([
                ['동', 'key_unit__houseunit__building_unit', 7],
                ['호수', 'key_unit__houseunit__name', 7]
            ])

        return headers

    def _get_applicant_queryset(self, request, project):
        """청약자 쿼리셋 생성"""
        return Contract.objects.filter(
            project=project,
            activation=True,
            contractor__status='1'
        ).order_by('contractor__reservation_date')

    def _write_applicant_data(self, worksheet, workbook, row_num, headers, queryset):
        """청약자 데이터 작성"""
        # 필드 추출 (빈 헤더 제외)
        params = []
        for header in headers:
            if header and header[1]:
                params.append(header[1])

        data = queryset.values_list(*params)

        for i, row in enumerate(data):
            for col_num, cell_data in enumerate(row):
                if col_num == 0:
                    cell_data = i + 1  # 순번

                # 기본 셀 포맷
                cell_format = workbook.add_format({
                    'border': True,
                    'valign': 'vcenter',
                    'align': 'center'
                })

                worksheet.write(row_num, col_num, cell_data, cell_format)

            row_num += 1


class ExportSuccessions(ExcelExportMixin, ProjectFilterMixin):
    """승계 리스트 Excel 내보내기"""

    def get(self, request):
        project = self.get_project(request)

        # Excel 워크북 생성
        output, workbook, worksheet = self.create_workbook('승계목록_정보')

        # 헤더 정의
        headers = self._get_succession_headers()

        # 제목 및 헤더 작성
        row_num = self.write_title(worksheet, workbook, 0, len(headers) - 1,
                                   f'{project} 승계 리스트')
        row_num = self.write_date_info(worksheet, workbook, row_num, len(headers) - 1)
        row_num = self.write_headers(worksheet, workbook, row_num, headers)

        # 데이터 조회 및 작성
        queryset = self._get_succession_queryset(request, project)
        self.write_data_rows(worksheet, workbook, row_num, headers, queryset)

        # 응답 생성
        filename = create_filename('successions', project.name)
        return self.create_response(output, workbook, filename)

    def _get_succession_headers(self):
        """승계 헤더 정의"""
        return [
            [],
            ['일련번호', 'contract__serial_number', 10],
            ['승계자', 'contractor__name', 10],
            ['승계타입', 'contractor__status', 8],
            ['승계일자', 'contractor__contract_date', 12],
            ['피승계자', 'prev_contractor__name', 10],
            ['연락처', 'contractor__contractorcontact__cell_phone', 14],
            ['비고', 'note', 30]
        ]

    def _get_succession_queryset(self, request, project):
        """승계 쿼리셋 생성"""
        return Succession.objects.filter(
            contract__project=project
        ).order_by('-created')


class ExportReleases(ExcelExportMixin, ProjectFilterMixin):
    """해약 리스트 Excel 내보내기"""

    def get(self, request):
        project = self.get_project(request)

        # Excel 워크북 생성
        output, workbook, worksheet = self.create_workbook('해약목록_정보')

        # 헤더 정의
        headers = self._get_release_headers()

        # 제목 및 헤더 작성
        row_num = self.write_title(worksheet, workbook, 0, len(headers) - 1,
                                   f'{project} 해약 리스트')
        row_num = self.write_date_info(worksheet, workbook, row_num, len(headers) - 1)
        row_num = self.write_headers(worksheet, workbook, row_num, headers)

        # 데이터 조회 및 작성
        queryset = self._get_release_queryset(request, project)
        self.write_data_rows(worksheet, workbook, row_num, headers, queryset)

        # 응답 생성
        filename = create_filename('releases', project.name)
        return self.create_response(output, workbook, filename)

    def _get_release_headers(self):
        """해약 헤더 정의"""
        return [
            [],
            ['일련번호', 'contract__serial_number', 10],
            ['해약자', 'contractor__name', 10],
            ['해약일자', 'refund_date', 12],
            ['해약사유', 'refund_reason', 15],
            ['위약금', 'penalty', 12],
            ['환불금액', 'refund_amount', 12],
            ['연락처', 'contractor__contractorcontact__cell_phone', 14],
            ['비고', 'note', 30]
        ]

    def _get_release_queryset(self, request, project):
        """해약 쿼리셋 생성"""
        return ContractorRelease.objects.filter(
            contract__project=project
        ).order_by('-refund_date')


class ExportUnitStatus(ExcelExportMixin, ProjectFilterMixin):
    """동호수 현황표 Excel 내보내기"""

    def get(self, request):
        project = self.get_project(request)
        is_contor = request.GET.get('iscontor') == 'true'

        # Excel 워크북 생성
        output, workbook, worksheet = self.create_workbook('동호수현황표')
        worksheet.set_default_row(15)

        # 데이터 조회
        max_floor = HouseUnit.objects.aggregate(Max('floor_no'))
        floor_no__max = max_floor['floor_no__max'] if max_floor['floor_no__max'] else 1
        max_floor_range = range(0, floor_no__max)
        unit_numbers = HouseUnit.objects.filter(building_unit__project=project)
        dong_obj = BuildingUnit.objects.filter(project=project).values('name')

        # 제목 작성
        row_num = self.write_title(worksheet, workbook, 0, 0, f'{project} 동호수 현황표')

        # 날짜 정보 계산
        max_col = 0
        for dong in dong_obj:
            lines = unit_numbers.order_by('bldg_line').values('bldg_line').filter(
                building_unit__name__contains=dong['name']).distinct()
            for line in lines:
                max_col += 1
            max_col += 1

        row_num = self.write_date_info(worksheet, workbook, 1, max_col)

        # 동호수 현황표 생성
        self._write_unit_status_board(
            worksheet, workbook, 3, project, max_floor_range, floor_no__max,
            unit_numbers, dong_obj, is_contor
        )

        # 동 제목 표시
        self._write_dong_titles(
            worksheet, workbook, max_floor_range, unit_numbers, dong_obj
        )

        # 응답 생성
        filename = create_filename('unit-status-board', project.name)
        return self.create_response(output, workbook, filename)

    def _write_unit_status_board(self, worksheet, workbook, row_num, project,
                                 max_floor_range, floor_no__max, unit_numbers, dong_obj, is_contor):
        """동호수 현황표 작성"""
        # 컬럼 설정
        max_col = 0
        for dong in dong_obj:
            lines = unit_numbers.order_by('bldg_line').values('bldg_line').filter(
                building_unit__name__contains=dong['name']).distinct()
            max_col += lines.count() + 1

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

    def _write_dong_titles(self, worksheet, workbook, max_floor_range, unit_numbers, dong_obj):
        """동 제목 표시"""
        row_num = len(max_floor_range) * 2 + 5
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
