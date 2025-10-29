import datetime
import io

import xlsxwriter
from django.db.models import Q
from django.http import HttpResponse

from _excel.mixins import ExcelExportMixin, AdvancedExcelMixin
from project.models import Project, Site, SiteOwner, SiteContract

TODAY = datetime.date.today().strftime('%Y-%m-%d')


class ExportSites(ExcelExportMixin, AdvancedExcelMixin):
    """프로젝트 지번별 토지목록"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('지번별_토지목록')

        formats = self.create_format_objects(workbook)
        body_format = {
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0',
        }

        # data start --------------------------------------------- #

        # -------------------- get_queryset start -------------------- #
        project = Project.objects.get(pk=request.GET.get('project'))
        search = request.GET.get('search')
        rights = request.GET.get('rights')
        obj_list = Site.objects.filter(project=project).order_by('order')
        obj_list = obj_list.filter(
            Q(district__icontains=search) |
            Q(lot_number__icontains=search) |
            Q(site_purpose__icontains=search) |
            Q(owners__owner__icontains=search)
        ) if search else obj_list
        # -------------------- get_queryset finish -------------------- #

        rows_cnt = 9 if project.is_returned_area else 7
        rows_cnt = rows_cnt if not rights else rows_cnt + 2

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)

        worksheet.merge_range(row_num, 0, row_num, rows_cnt, str(project) + ' 토지목록 조서', formats['title'])

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, rows_cnt, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header
        row_num = 2
        worksheet.set_row(row_num, 23, workbook.add_format({'bold': True}))

        # Header_contents
        at = '소유면적'
        area_title = at + '(환지면적 기준)' if project.is_returned_area else at
        header_src = [
            ['No', 'order', 10],
            ['행정동', 'district', 15],
            ['지번', 'lot_number', 15],
            ['지목', 'site_purpose', 12],
            ['대지면적', 'official_area', 13],
            ['', '', 13],
        ]

        if project.is_returned_area:
            header_src.append(['환지면적', 'returned_area', 13])
            header_src.append(['', '', 13])

        header_src.append(['공시지가', 'notice_price', 14])

        if rights:
            header_src.append(['갑구 권리제한사항', 'rights_a', 18])
            header_src.append(['을구 권리제한사항', 'rights_b', 18])

        header_src.append(['비고', 'note', 30])

        titles = []  # 헤더명
        params = []  # 헤더 컬럼(db)
        widths = []  # 헤더 넓이

        for src in header_src:  # 요청된 컬럼 개수 만큼 반복 (1-2-3... -> i)
            titles.append(src[0])  # 헤더명
            params.append(src[1])  # 헤더 컬럼(db)
            widths.append(src[2])  # 헤더 넓이

        # Adjust the column width.
        for i, cw in enumerate(widths):  # 각 컬럼 넙이 세팅
            worksheet.set_column(i, i, cw)

        # Write header
        area_col_num = (4, 5, 6, 7) if project.is_returned_area else (4, 5)

        for col_num, title in enumerate(titles):  # 헤더 줄 제목 세팅
            if '면적' in title:
                worksheet.merge_range(row_num, col_num, row_num, col_num + 1, title, formats['header'])
            elif int(col_num) not in area_col_num:
                worksheet.merge_range(row_num, col_num, row_num + 1, col_num, title, formats['header'])

        row_num = 3
        worksheet.set_row(row_num, 23, workbook.add_format({'bold': True}))

        area_col1 = (4, 6) if project.is_returned_area else (4,)
        area_col2 = (5, 7) if project.is_returned_area else (5,)
        for col_num, title in enumerate(titles):
            if int(col_num) in area_col1:
                worksheet.write(row_num, col_num, '㎡', formats['header'])
            elif int(col_num) in area_col2:
                worksheet.write(row_num, col_num, '평', formats['header'])

        #################################################################
        # 4. Body
        # Get some data to write to the spreadsheet.

        while '' in params:
            params.remove('')

        rows = obj_list.values_list(*params)

        # Turn off some of the warnings:
        worksheet.ignore_errors({'number_stored_as_text': 'C:D'})

        for row in rows:
            row_num += 1
            row = list(row)

            for col_num, title in enumerate(titles):
                left_col_num = 8 if project.is_returned_area else 6
                if col_num > left_col_num:
                    body_format['align'] = 'left'
                elif col_num == left_col_num:
                    body_format['align'] = 'right'
                else:
                    body_format['align'] = 'center'
                # css 정렬
                if col_num in area_col_num:
                    body_format['num_format'] = 43
                else:
                    body_format['num_format'] = '#,##0'

                bf = workbook.add_format(body_format)

                if col_num < 5:
                    worksheet.write(row_num, col_num, row[col_num], bf)
                elif col_num == 5:
                    worksheet.write(row_num, col_num, float(row[col_num - 1]) * 0.3025, bf)
                else:
                    if project.is_returned_area:
                        if col_num == 6:
                            worksheet.write(row_num, col_num, row[col_num - 1], bf)
                        elif col_num == 7:
                            worksheet.write(row_num, col_num, float(row[col_num - 2]) * 0.3025, bf)
                        else:
                            worksheet.write(row_num, col_num, row[col_num - 2], bf)
                    else:
                        worksheet.write(row_num, col_num, row[col_num - 1], bf)

        row_num += 1
        worksheet.set_row(row_num, 23)

        sum_area = sum([a[4] for a in rows])
        sum_ret_area = sum([a[5] for a in rows]) if project.is_returned_area else None

        for col_num, title in enumerate(titles):
            # css 정렬
            sum_format = workbook.add_format(body_format)
            sum_format.set_bold()
            sum_format.set_bg_color('#eeeeee')

            if col_num in area_col_num:
                sum_format.set_num_format(43)

            if col_num == 0:
                worksheet.merge_range(row_num, 0, row_num, 1, '합계', sum_format)
            elif col_num in (2, 3):
                worksheet.write(row_num, col_num, '', sum_format)
            elif col_num == 4:
                worksheet.write(row_num, col_num, sum_area, sum_format)
            elif col_num == 5:
                worksheet.write(row_num, col_num, float(sum_area) * 0.3025, sum_format)
            else:
                if project.is_returned_area:
                    if col_num == 6:
                        worksheet.write(row_num, col_num, sum_ret_area, sum_format)
                    elif col_num == 7:
                        worksheet.write(row_num, col_num, float(sum_ret_area) * 0.3025, sum_format)
                    else:
                        worksheet.write(row_num, col_num, '', sum_format)
                else:
                    worksheet.write(row_num, col_num, '', sum_format)
        #################################################################

        # data finish -------------------------------------------- #

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = request.GET.get('filename', 'sites')
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportSitesByOwner(ExcelExportMixin, AdvancedExcelMixin):
    """프로젝트 소유자별 토지목록"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('소유자별_토지목록')
        formats = self.create_format_objects(workbook)

        # data start --------------------------------------------- #

        # -------------------- get_queryset start -------------------- #
        project = Project.objects.get(pk=request.GET.get('project'))
        own_sort = request.GET.get('own_sort')
        search = request.GET.get('search')
        obj_list = SiteOwner.objects.prefetch_related('sites', 'relations__site').filter(project=project).order_by('id')
        obj_list = obj_list.filter(own_sort=own_sort) if own_sort else obj_list
        obj_list = obj_list.filter(
            Q(owner__icontains=search) |
            Q(phone1__icontains=search) |
            Q(phone2__icontains=search) |
            Q(sites__lot_number__icontains=search) |
            Q(note__icontains=search)
        ) if search else obj_list
        # -------------------- get_queryset finish -------------------- #

        rows_cnt = 9

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)

        worksheet.merge_range(row_num, 0, row_num, rows_cnt, str(project) + ' 소유자목록 조서', formats['title'])

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, rows_cnt, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header
        row_num = 2
        worksheet.set_row(row_num, 25, workbook.add_format({'bold': True}))

        # Header_contents
        at = '소유면적'
        area_title = at + '(환지면적 기준)' if project.is_returned_area else at
        header_src = [
            ['소유구분', 'own_sort', 10],
            ['소유자', 'owner', 18],
            ['생년월일', 'date_of_birth', 15],
            ['주연락처', 'phone1', 18],
            ['소유부지(지번)', 'sites__lot_number', 12],
            ['소유지분(%)', 'relations__ownership_ratio', 10],
            [area_title, 'relations__owned_area', 12],
            ['', '', 12],
            ['취득일자', 'relations__acquisition_date', 15],
            ['사용동의', 'use_consent', 12]
        ]

        titles = []  # 헤더명
        # params = []  # 헤더 컬럼(db)
        widths = []  # 헤더 넓이

        for src in header_src:  # 요청된 컬럼 개수 만큼 반복 (1-2-3... -> i)
            titles.append(src[0])  # 일련번호
            widths.append(src[2])  # 10

        # Adjust the column width.
        for i, cw in enumerate(widths):  # 각 컬럼 넙이 세팅
            worksheet.set_column(i, i, cw)

        # Write header
        for col_num, col in enumerate(titles):  # 헤더 줄 제목 세팅
            if '면적' in col:
                worksheet.merge_range(row_num, col_num, row_num, col_num + 1, titles[col_num], formats['header'])
            elif int(col_num) not in (6, 7):
                worksheet.merge_range(row_num, col_num, row_num + 1, col_num, titles[col_num], formats['header'])

        row_num = 3

        for col_num, col in enumerate(titles):
            if int(col_num) == 6:
                worksheet.write(row_num, col_num, '㎡', formats['header'])
            elif int(col_num) == 7:
                worksheet.write(row_num, col_num, '평', formats['header'])

        #################################################################
        # 4. Body
        # Get some data to write to the spreadsheet.
        body_format = {
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0.00',
        }

        # while '' in params:
        #     params.remove('')

        # rows = obj_list.values_list(*params)
        rows = []
        for owner in obj_list:
            site_count = owner.sites.count()

            for relation in owner.relations.all():
                lot_number = relation.site.lot_number
                ownership_ratio = relation.ownership_ratio
                owned_area = relation.owned_area
                acquisition_date = relation.acquisition_date

                row = (site_count, owner.own_sort, owner.owner, owner.date_of_birth,
                       owner.phone1, lot_number, ownership_ratio, owned_area,
                       acquisition_date, owner.use_consent)
                rows.append(row)

        # Turn off some of the warnings:
        worksheet.ignore_errors({'number_stored_as_text': 'D:E'})

        for row in rows:
            row_num += 1
            for col_num, cell_data in enumerate(titles):
                row = list(row)

                # format setting
                if col_num in (2, 8):
                    body_format['num_format'] = 'yyyy-mm-dd'

                if col_num in (5, 6, 7):
                    body_format['num_format'] = 43

                bf = workbook.add_format(body_format)

                # value setting
                if col_num == 0:
                    cell_value = self.get_sort(row[col_num + 1])
                elif col_num < 7:
                    cell_value = row[col_num + 1]
                elif col_num == 7:
                    cell_value = float(row[col_num] or 0) * 0.3025
                elif col_num == 8:
                    cell_value = row[col_num]
                else:
                    cell_value = '동의' if row[col_num] else ''

                # merge setting
                if col_num not in (4, 5, 6, 7, 8, 9):
                    if row[0] > 1:
                        try:
                            worksheet.merge_range(row_num, col_num, row_num + row[0] - 1, col_num, cell_value, bf)
                        except Exception:
                            pass
                    else:
                        worksheet.write(row_num, col_num, cell_value, bf)
                else:
                    worksheet.write(row_num, col_num, cell_value, bf)

        row_num += 1
        worksheet.set_row(row_num, 23)

        sum_area = sum([a[7] or 0 for a in rows])  # 면적 합계

        for col_num, title in enumerate(titles):
            # css 정렬
            sum_format = workbook.add_format(body_format)
            sum_format.set_bold()
            sum_format.set_border()
            sum_format.set_num_format(43)
            sum_format.set_bg_color('#eeeeee')

            if col_num == 0:
                worksheet.merge_range(row_num, 0, row_num, 1, '합계', sum_format)
            elif col_num == 6:
                worksheet.write(row_num, col_num, sum_area, sum_format)
            elif col_num == 7:
                worksheet.write(row_num, col_num, float(sum_area or 0) * 0.3025, sum_format)
            else:
                worksheet.write(row_num, col_num, None, sum_format)
        #################################################################

        # data finish -------------------------------------------- #

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = request.GET.get('filename', 'sites-by-owner')
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)

    @staticmethod
    def get_sort(code):
        sort = ('', '개인', '법인', '국공유지')
        return sort[int(code)]


class ExportSitesContracts(ExcelExportMixin, AdvancedExcelMixin):
    """프로젝트 토지 계약현황"""

    def get(self, request):
        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('사업부지_계약현황')

        worksheet.set_default_row(20)  # 기본 행 높이

        # data start --------------------------------------------- #

        # --------------------- get_queryset start --------------------- #
        project = Project.objects.get(pk=request.GET.get('project'))
        own_sort = request.GET.get('own_sort')
        search = request.GET.get('search')
        obj_list = SiteContract.objects.filter(project=project).order_by('owner__id')
        obj_list = obj_list.filter(owner__own_sort=own_sort) if own_sort else obj_list
        obj_list = obj_list.filter(
            Q(owner__owner__icontains=search) |
            Q(owner__phone1__icontains=search) |
            Q(acc_bank__icontains=search) |
            Q(acc_owner__icontains=search) |
            Q(note__icontains=search)
        ) if search else obj_list
        # --------------------- get_queryset finish --------------------- #

        rows_cnt = 18

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)

        title_format = workbook.add_format()
        title_format.set_font_size(18)
        title_format.set_align('vcenter')
        title_format.set_bold()
        worksheet.merge_range(row_num, 0, row_num, rows_cnt, str(project) + ' 사업부지 계약현황', title_format)

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, rows_cnt, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header
        row_num = 2
        worksheet.set_row(row_num, 25, workbook.add_format({'bold': True}))

        header_format = workbook.add_format()
        header_format.set_bold()
        header_format.set_border()
        header_format.set_align('center')
        header_format.set_align('vcenter')
        header_format.set_bg_color('#eeeeee')

        # Header_contents
        header_src = [['소유구분', 'owner__own_sort', 8],
                      ['소유자', 'owner__owner', 18],
                      ['계약일', 'contract_date', 15],
                      ['총 계약면적', 'contract_area', 10],
                      ['', '', 10],
                      ['총 매매대금', 'total_price', 16],
                      ['계약금1', 'down_pay1', 13],
                      ['지급일', 'down_pay1_date', 13],
                      ['지급여부', 'down_pay1_is_paid', 9],
                      ['계약금2', 'down_pay2', 13],
                      ['지급일', 'down_pay2_date', 13],
                      ['중도금1', 'inter_pay1', 13],
                      ['지급일', 'inter_pay1_date', 13],
                      ['중도금2', 'inter_pay2', 13],
                      ['지급일', 'inter_pay2_date', 13],
                      ['잔금', 'remain_pay', 15],
                      ['지급일', 'remain_pay_date', 13],
                      ['지급여부', 'remain_pay_is_paid', 9],
                      ['비고', 'note', 30]]

        titles = []  # 헤더명
        params = []  # 헤더 컬럼(db)
        widths = []  # 헤더 넓이

        for src in header_src:  # 요청된 컬럼 개수 만큼 반복 (1-2-3... -> i)
            titles.append(src[0])  # 일련번호
            params.append(src[1])  # serial_number
            widths.append(src[2])  # 10

        # Adjust the column width.
        for i, cw in enumerate(widths):  # 각 컬럼 넙이 세팅
            worksheet.set_column(i, i, cw)

        # Write header
        last_col = 0
        for col_num, col in enumerate(titles):  # 헤더 줄 제목 세팅
            if '면적' in col:
                worksheet.merge_range(row_num, col_num, row_num, col_num + 1, titles[col_num], header_format)
            elif int(col_num) not in (3, 4):
                worksheet.merge_range(row_num, col_num, row_num + 1, col_num, titles[col_num], header_format)
            if '비고' in col:
                last_col = col_num

        row_num = 3

        for col_num, col in enumerate(titles):
            if int(col_num) == 3:
                worksheet.write(row_num, col_num, '㎡', header_format)
            elif int(col_num) == 4:
                worksheet.write(row_num, col_num, '평', header_format)

        #################################################################
        # 4. Body
        # Get some data to write to the spreadsheet.

        body_format = {
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': 'yyyy-mm-dd',
        }

        while '' in params:
            params.remove('')

        rows = obj_list.values_list(*params)

        for row in rows:
            row_num += 1
            for col_num, cell_data in enumerate(titles):
                row = list(row)
                if col_num == last_col:
                    body_format['align'] = 'left'
                else:
                    body_format['align'] = 'center'
                if col_num in (2, 7, 10, 12, 14, 16):
                    body_format['num_format'] = 'yyyy-mm-dd'
                elif col_num in (3, 4):
                    body_format['num_format'] = 43
                else:
                    body_format['num_format'] = 41
                bf = workbook.add_format(body_format)

                if col_num == 0:
                    worksheet.write(row_num, col_num, self.get_sort(row[col_num]), bf)
                elif col_num == 4:
                    worksheet.write(row_num, col_num, float(row[col_num - 1]) * 0.3025, bf)
                else:
                    if col_num < 5:
                        worksheet.write(row_num, col_num, self.get_row_content(row[col_num]), bf)
                    else:
                        worksheet.write(row_num, col_num, self.get_row_content(row[col_num - 1]), bf)

        row_num += 1
        worksheet.set_row(row_num, 23)

        sum_cont_area = sum([a[3] for a in rows])
        sum_cont_price = sum([a[4] for a in rows])
        sum_cont_down1 = sum([a[5] or 0 for a in rows])
        sum_cont_down2 = sum([a[8] or 0 for a in rows])
        sum_cont_inter1 = sum([a[10] or 0 for a in rows])
        sum_cont_inter2 = sum([a[12] or 0 for a in rows])
        sum_cont_rmain = sum([a[14] or 0 for a in rows])

        for col_num, title in enumerate(titles):
            # css 정렬
            sum_format = workbook.add_format(body_format)
            sum_format.set_bold()
            sum_format.set_border()
            sum_format.set_num_format(41)
            sum_format.set_bg_color('#eeeeee')

            if col_num == 0:
                worksheet.merge_range(row_num, 0, row_num, 1, '합계', sum_format)
            elif col_num == 3:
                sum_format.set_num_format(43)
                worksheet.write(row_num, col_num, sum_cont_area, sum_format)
            elif col_num == 4:
                sum_format.set_num_format(43)
                worksheet.write(row_num, col_num, float(sum_cont_area) * 0.3025, sum_format)
            elif col_num == 5:
                sum_format.set_num_format(41)
                worksheet.write(row_num, col_num, sum_cont_price, sum_format)
            elif col_num == 6:
                worksheet.write(row_num, col_num, sum_cont_down1, sum_format)
            elif col_num == 9:
                worksheet.write(row_num, col_num, sum_cont_down2, sum_format)
            elif col_num == 11:
                worksheet.write(row_num, col_num, sum_cont_inter1, sum_format)
            elif col_num == 13:
                worksheet.write(row_num, col_num, sum_cont_inter2, sum_format)
            elif col_num == 15:
                worksheet.write(row_num, col_num, sum_cont_rmain, sum_format)
            else:
                worksheet.write(row_num, col_num, None, sum_format)
        #################################################################

        # data end ----------------------------------------------- #

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = f'{TODAY}-sites-contracts.xlsx'
        file_format = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = HttpResponse(output, content_type=file_format)
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response

    @staticmethod
    def get_sort(code):
        sort = ('', '개인', '법인', '국공유지')
        return sort[int(code)]

    @staticmethod
    def get_row_content(cont):
        if type(cont) == bool:
            return '완료' if cont else ''
        else:
            return cont
