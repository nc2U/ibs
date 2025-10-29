import datetime
import io

import xlsxwriter
from django.db.models import Q
from django.http import HttpResponse

from _excel.mixins import ExcelExportMixin
from company.models import Company
from docs.models import LawsuitCase
from project.models import Project

TODAY = datetime.date.today().strftime('%Y-%m-%d')


class ExportSuitCases(ExcelExportMixin):
    """PR 소송 사건 목록"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('소송_목록')

        # data start --------------------------------------------- #
        com_id = request.GET.get('company')
        company = Company.objects.get(pk=com_id) if com_id else None
        proj_id = request.GET.get('project')
        project = Project.objects.get(pk=proj_id) if proj_id else None

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)
        body_format = {
            'border': True,
            'valign': 'vcenter',
            'num_format': '#,##0'
        }

        # title_list
        header_src = [[],
                      ['종류', 'sort', 10],
                      ['심급', 'level', 10],
                      ['관련사건', 'related_case', 16],
                      ['처리기관', 'other_agency', 15],
                      ['관할법원', 'court', 22],
                      ['사건번호', 'case_number', 16],
                      ['사건명', 'case_name', 25],
                      ['원고(채권자)', 'plaintiff', 25],
                      ['원고측대리인', 'plaintiff_attorney', 45],
                      ['원고 소가', 'plaintiff_case_price', 20],
                      ['피고(채무자)', 'defendant', 25],
                      ['피고측대리인', 'defendant_attorney', 45],
                      ['피고 소가', 'defendant_case_price', 20],
                      ['제3채무자', 'related_debtor', 20],
                      ['사건개시일', 'case_start_date', 14],
                      ['사건종결일', 'case_end_date', 14],
                      ['개요 및 경과', 'summary', 45]]

        titles = ['No']  # header titles
        params = []  # ORM 추출 field
        widths = [7]  # No. 컬럼 넓이

        for el in header_src:
            if el:
                titles.append(el[0])
                params.append(el[1])
                widths.append(el[2])

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1,
                              str(project if project else company) + ' 소송사건 목록',
                              title_format)

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header - 1
        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

        # Adjust the column width.
        for i, col_width in enumerate(widths):
            worksheet.set_column(i, i, col_width)

        # Write header - 1
        for col_num, title in enumerate(titles):
            worksheet.write(row_num, col_num, title, h_format)

        # 4. Body
        # Get some data to write to the spreadsheet.
        obj_list = LawsuitCase.objects.filter(issue_project__company=company)

        is_com = request.GET.get('is_com')
        sort = request.GET.get('sort')
        level = request.GET.get('level')
        court = request.GET.get('court')
        in_progress = request.GET.get('in_progress')

        obj_list = obj_list.filter(project__isnull=True) if is_com == 'true' else obj_list
        obj_list = obj_list.filter(project=project) if project and is_com == 'false' else obj_list
        obj_list = obj_list.filter(case_end_date__isnull=True) if in_progress == 'true' else obj_list
        obj_list = obj_list.filter(case_end_date__isnull=False) if in_progress == 'false' else obj_list
        obj_list = obj_list.filter(sort=sort) if sort else obj_list
        obj_list = obj_list.filter(level=level) if level else obj_list
        obj_list = obj_list.filter(court=court) if court else obj_list

        search = request.GET.get('search')
        if search:
            obj_list = obj_list.filter(
                Q(other_agency__icontains=search) |
                Q(case_number__icontains=search) |
                Q(case_name__icontains=search) |
                Q(plaintiff__icontains=search) |
                Q(defendant__icontains=search) |
                Q(case_start_date__icontains=search) |
                Q(case_end_date__icontains=search) |
                Q(summary__icontains=search))

        data = obj_list.values_list(*params)

        # Turn off some of the warnings:
        # worksheet.ignore_errors({'number_stored_as_text': 'F:G'})

        def get_related_case(pk):
            rs_case = LawsuitCase.objects.get(pk=pk)
            return rs_case.case_number

        # Write body
        for i, row in enumerate(data):
            row = list(row)
            row_num += 1
            row.insert(0, i + 1)
            for col_num, cell_data in enumerate(row):
                if col_num == 1:
                    cell_data = list(filter(lambda x: x[0] == cell_data, LawsuitCase.SORT_CHOICES))[0][1]
                elif col_num == 2:
                    cell_data = list(filter(lambda x: x[0] == cell_data, LawsuitCase.LEVEL_CHOICES))[0][1]
                elif col_num == 3:
                    cell_data = get_related_case(cell_data) if cell_data else ''
                elif col_num == 5:
                    cell_data = list(filter(lambda x: x[0] == cell_data, LawsuitCase.COURT_CHOICES))[0][1] \
                        if cell_data else ''
                if col_num < 6 or col_num in (15, 16):
                    if col_num in (15, 16):
                        body_format['num_format'] = 'yyyy-mm-dd'
                    else:
                        body_format['num_format'] = '#,##0'
                    body_format['align'] = 'center'
                    bformat = workbook.add_format(body_format)
                    worksheet.write(row_num, col_num, cell_data, bformat)
                else:
                    body_format['align'] = 'left'
                    bformat = workbook.add_format(body_format)
                    worksheet.write(row_num, col_num, cell_data, bformat)

        # data finish -------------------------------------------- #

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = request.GET.get('filename') or 'successions'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportSuitCase(ExcelExportMixin):
    """PR 소송 사건 디테일"""

    @staticmethod
    def get(request):
        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('소송 사건')

        worksheet.set_default_row(25)  # 기본 행 높이

        # data start --------------------------------------------- #
        obj = LawsuitCase.objects.get(pk=request.GET.get('pk'))

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)
        title_format = workbook.add_format()
        title_format.set_bold()
        title_format.set_font_size(18)
        title_format.set_align('vcenter')
        worksheet.merge_range(row_num, 0, row_num, 3, str(obj), title_format)

        # 3. Header - 1
        row_num = 1
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

        h_format = workbook.add_format()
        h_format.set_bold()
        h_format.set_border()
        h_format.set_align('center')
        h_format.set_align('vcenter')
        h_format.set_bg_color('#eeeeee')

        # Adjust the column width.
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 50)
        worksheet.set_column(2, 2, 20)
        worksheet.set_column(3, 3, 50)

        # 4. Body

        h_format = workbook.add_format()
        h_format.set_border()
        h_format.set_align('center')
        h_format.set_align('vcenter')
        h_format.set_bg_color('#EEEEEE')

        b_format = workbook.add_format()
        b_format.set_border()
        b_format.set_align('vcenter')
        b_format.set_num_format('yyyy-mm-dd')

        c_format = workbook.add_format()
        c_format.set_border()
        c_format.set_align('vcenter')
        c_format.set_num_format('#,##0')

        # Turn off the warnings:
        worksheet.ignore_errors({'number_stored_as_text': 'B:D'})

        # table header
        row_num = 2
        worksheet.write(row_num, 0, '구분', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3, '내용', h_format)

        row_num = 3
        worksheet.write(row_num, 0, '사건 번호', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3, str(obj.case_number), b_format)

        row_num = 4
        worksheet.write(row_num, 0, '사건명', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3, str(obj.case_name), b_format)

        row_num = 5
        worksheet.write(row_num, 0, '유형', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3,
                              list(filter(lambda x: x[0] == obj.sort, LawsuitCase.SORT_CHOICES))[0][1],
                              b_format)

        row_num = 6
        worksheet.write(row_num, 0, '심급', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3,
                              list(filter(lambda x: x[0] == obj.level, LawsuitCase.LEVEL_CHOICES))[0][1],
                              b_format)

        row_num = 7
        worksheet.write(row_num, 0, '관련 사건', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3, str(obj.related_case), b_format)

        row_num = 8
        worksheet.write(row_num, 0, '관할 법원', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3,
                              list(filter(lambda x: x[0] == obj.court, LawsuitCase.COURT_CHOICES))[0][1] \
                                  if obj.court else '',
                              b_format)

        row_num = 9
        worksheet.write(row_num, 0, '처리기관', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3, str(obj.other_agency), b_format)

        row_num = 10
        worksheet.write(row_num, 0, '원고(채권자)', h_format)
        worksheet.write(row_num, 1, str(obj.plaintiff), b_format)
        worksheet.write(row_num, 2, '피고(채무자)', h_format)
        worksheet.write(row_num, 3, str(obj.defendant), b_format)

        row_num = 11
        worksheet.write(row_num, 0, '원고측 대리인', h_format)
        worksheet.write(row_num, 1, str(obj.plaintiff_attorney), b_format)
        worksheet.write(row_num, 2, '피고측 대리인', h_format)
        worksheet.write(row_num, 3, str(obj.defendant_attorney), b_format)

        row_num = 12
        worksheet.write(row_num, 0, '원고 소가', h_format)
        worksheet.write(row_num, 1, obj.plaintiff_case_price, c_format)
        worksheet.write(row_num, 2, '피고 소가', h_format)
        worksheet.write(row_num, 3, obj.defendant_case_price, c_format)

        row_num = 13
        worksheet.write(row_num, 0, '제3채무자', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3, str(obj.related_debtor), b_format)

        row_num = 14
        worksheet.write(row_num, 0, '사건개시일', h_format)
        worksheet.write(row_num, 1, str(obj.case_start_date), b_format)
        worksheet.write(row_num, 2, '사건종결일', h_format)
        worksheet.write(row_num, 3, str(obj.case_end_date) if obj.case_end_date else '', b_format)

        row_num = 15
        worksheet.write(row_num, 0, '개요 및 경과', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3, str(obj.summary), b_format)

        # data finish -------------------------------------------- #

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = f'{TODAY}-suitcase.xlsx'
        file_format = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = HttpResponse(output, content_type=file_format)
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response
