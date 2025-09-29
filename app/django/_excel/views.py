##############################################################################
#
# A Django view class to write an Excel file using the XlsxWriter
# module.
#
# Copyright 2013-2020, John McNamara, jmcnamara@cpan.org
#
import datetime
import io
import json

import xlsxwriter
import xlwt
from django.core import serializers
from django.db.models import Q, F, Sum, When, Case, PositiveBigIntegerField
from django.http import HttpResponse
from django.views.generic import View

from cash.models import CashBook, ProjectCashBook
from company.models import Company, Staff, Department, JobGrade, Position, DutyTitle
from contract.models import Contract
from docs.models import LawsuitCase
from project.models import Project, ProjectOutBudget, Site, SiteOwner, SiteContract

TODAY = datetime.date.today().strftime('%Y-%m-%d')


class ExportStaffs(View):
    """직원 목록 정보"""

    @staticmethod
    def get(request):
        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('직원 정보')

        worksheet.set_default_row(20)  # 기본 행 높이

        # data start --------------------------------------------- #
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        # title_list
        header_src = [[],
                      ['구분', 'sort', 10],
                      ['직원명', 'name', 12],
                      ['주민등록번호', 'id_number', 18],
                      ['휴대전화', 'personal_phone', 17],
                      ['이메일', 'email', 22],
                      ['부서', 'department', 12],
                      ['직급', 'grade', 12],
                      ['직위', 'position', 13],
                      ['직책', 'duty', 13],
                      ['입사일', 'date_join', 15],
                      ['상태', 'status', 13],
                      ['퇴사일', 'date_leave', 15]]
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
        title_format = workbook.add_format()
        title_format.set_bold()
        title_format.set_font_size(18)
        title_format.set_align('vcenter')
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 직원 정보 목록', title_format)

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header - 1
        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

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
        obj_list = Staff.objects.filter(company=company)

        # get query list
        sort = request.GET.get('sort')
        department = request.GET.get('department')
        grade = request.GET.get('grade')
        position = request.GET.get('position')
        duty = request.GET.get('duty')
        status = request.GET.get('status')
        search = request.GET.get('search')

        obj_list = obj_list.filter(sort=sort) if sort else obj_list
        obj_list = obj_list.filter(department_id=department) if department else obj_list
        obj_list = obj_list.filter(grade_id=grade) if grade else obj_list
        obj_list = obj_list.filter(position_id=position) if position else obj_list
        obj_list = obj_list.filter(duty_id=duty) if duty else obj_list
        obj_list = obj_list.filter(status=status) if status else obj_list
        obj_list = obj_list.filter(
            Q(name__icontains=search) |
            Q(id_number__icontains=search) |
            Q(personal_phone__icontains=search) |
            Q(email__icontains=search)) if search else obj_list

        data = obj_list.values_list(*params)

        b_format = workbook.add_format()
        b_format.set_border()
        b_format.set_align('center')
        b_format.set_align('vcenter')
        b_format.set_num_format('yyyy-mm-dd')

        body_format = {
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': 'yyyy-mm-dd'
        }

        # Turn off some of the warnings:
        worksheet.ignore_errors({'number_stored_as_text': 'B:L'})

        # Write body
        sort = dict(Staff.SORT_CHOICES)
        status = dict(Staff.STATUS_CHOICES)
        for i, row in enumerate(data):
            row = list(row)
            row_num += 1
            row.insert(0, i + 1)
            for col_num, cell_data in enumerate(row):
                if col_num == 1:
                    cell_data = sort[cell_data]
                if col_num == 6:
                    cell_data = Department.objects.get(pk=cell_data).name if cell_data else None
                if col_num == 7:
                    cell_data = JobGrade.objects.get(pk=cell_data).name if cell_data else None
                if col_num == 8:
                    cell_data = Position.objects.get(pk=cell_data).name if cell_data else None
                if col_num == 9:
                    cell_data = DutyTitle.objects.get(pk=cell_data).name if cell_data else None
                if col_num == 11:
                    cell_data = status[cell_data]
                if col_num in (10, 12):
                    body_format['num_format'] = 'yyyy-mm-dd'
                else:
                    body_format['num_format'] = '#,##0'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)

        # data finish -------------------------------------------- #

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = f'{TODAY}-staffs.xlsx'
        file_format = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = HttpResponse(output, content_type=file_format)
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response


class ExportDeparts(View):
    """부서 목록 정보"""

    @staticmethod
    def get(request):
        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('부서 정보')

        worksheet.set_default_row(20)  # 기본 행 높이

        # data start --------------------------------------------- #
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        # title_list
        header_src = [[],
                      ['상위부서', 'upper_depart', 15],
                      ['부서명', 'name', 15],
                      ['주요 업무', 'task', 50]]
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
        title_format = workbook.add_format()
        title_format.set_bold()
        title_format.set_font_size(18)
        title_format.set_align('vcenter')
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 부서 정보 목록', title_format)

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header - 1
        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

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
        upper_depart = request.GET.get('upper_depart')
        search = request.GET.get('search')
        obj_list = Department.objects.filter(company=company)

        obj_list = obj_list.filter(upper_depart_id=upper_depart) if upper_depart else obj_list
        obj_list = obj_list.filter(
            Q(name__icontains=search) |
            Q(task__icontains=search)) if search else obj_list

        data = obj_list.values_list(*params)

        b_format = workbook.add_format()
        b_format.set_border()
        b_format.set_align('center')
        b_format.set_align('vcenter')
        b_format.set_num_format('yyyy-mm-dd')

        body_format = {
            'border': True,
            'valign': 'vcenter',
            'num_format': '#,##0'
        }

        # Turn off some of the warnings:
        # worksheet.ignore_errors({'number_stored_as_text': 'F:G'})

        # Write body
        for i, row in enumerate(data):
            row = list(row)
            row_num += 1
            row.insert(0, i + 1)
            for col_num, cell_data in enumerate(row):
                if col_num == 1:
                    cell_data = obj_list.get(pk=cell_data).name if cell_data else None
                if col_num == 3:
                    body_format['align'] = 'left'
                else:
                    body_format['align'] = 'center'

                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)

        # data finish -------------------------------------------- #

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = f'{TODAY}-departs.xlsx'
        file_format = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = HttpResponse(output, content_type=file_format)
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response


class ExportPositions(View):
    """직위 목록 정보"""

    @staticmethod
    def get(request):
        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('직위 정보')

        worksheet.set_default_row(20)  # 기본 행 높이

        # data start --------------------------------------------- #
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        # title_list
        header_src = [[],
                      ['직위명', 'name', 15],
                      ['직급', 'grades', 25],
                      ['설명', 'desc', 50]]
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
        title_format = workbook.add_format()
        title_format.set_bold()
        title_format.set_font_size(18)
        title_format.set_align('vcenter')
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 직원 정보 목록', title_format)

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header - 1
        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

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
        search = request.GET.get('search')
        obj_list = Position.objects.filter(company=company)
        obj_list = obj_list.filter(name__icontains=search) if search else obj_list

        json_data = serializers.serialize('json', obj_list)
        data = [i['fields'] for i in json.loads(json_data)]
        # data = obj_list.values_list(*params)

        b_format = workbook.add_format()
        b_format.set_border()
        b_format.set_align('center')
        b_format.set_align('vcenter')
        b_format.set_num_format('yyyy-mm-dd')

        body_format = {
            'border': True,
            'valign': 'vcenter',
            'num_format': '#,##0'
        }

        # Turn off some of the warnings:
        worksheet.ignore_errors({'number_stored_as_text': 'A:D'})

        def get_grade(pk):
            return JobGrade.objects.get(pk=pk).name

        # Write body
        params.insert(0, 'num')
        for i, row in enumerate(data):
            row_num += 1
            row['num'] = i + 1
            del row['company']
            row_data = []
            row_data.insert(0, row['num'])
            row_data.insert(1, row['name'])
            row_data.insert(2, row['grades'])
            row_data.insert(3, row['desc'])

            for col_num, cell_data in enumerate(row_data):
                if type(cell_data) == list:
                    grades = [get_grade(i) for i in cell_data]
                    cell_data = ', '.join(sorted(grades))
                if col_num in (2, 3):
                    body_format['align'] = 'left'
                else:
                    body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)
        # data finish -------------------------------------------- #

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = f'{TODAY}-positions.xlsx'
        file_format = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = HttpResponse(output, content_type=file_format)
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response


class ExportDuties(View):
    """직책 정보 목록"""

    @staticmethod
    def get(request):
        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('직책 정보')

        worksheet.set_default_row(20)  # 기본 행 높이

        # data start --------------------------------------------- #
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        # title_list
        header_src = [[],
                      ['직책명', 'name', 20],
                      ['설명', 'desc', 60]]
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
        title_format = workbook.add_format()
        title_format.set_bold()
        title_format.set_font_size(18)
        title_format.set_align('vcenter')
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 직책 정보 목록', title_format)

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header - 1
        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

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
        search = request.GET.get('search')
        obj_list = DutyTitle.objects.filter(company=company)
        obj_list = obj_list.filter(name__icontains=search) if search else obj_list

        data = obj_list.values_list(*params)

        b_format = workbook.add_format()
        b_format.set_border()
        b_format.set_align('center')
        b_format.set_align('vcenter')
        b_format.set_num_format('yyyy-mm-dd')

        body_format = {
            'border': True,
            'valign': 'vcenter',
            'num_format': '#,##0'
        }

        # Turn off some of the warnings:
        # worksheet.ignore_errors({'number_stored_as_text': 'F:G'})

        # Write body
        for i, row in enumerate(data):
            row = list(row)
            row_num += 1
            row.insert(0, i + 1)
            for col_num, cell_data in enumerate(row):
                if col_num == 3:
                    body_format['align'] = 'left'
                else:
                    body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)
        # data finish -------------------------------------------- #

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = f'{TODAY}-duties.xlsx'
        file_format = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = HttpResponse(output, content_type=file_format)
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response


class ExportGrades(View):
    """직급 정보 목록"""

    @staticmethod
    def get(request):
        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('직급 정보')

        worksheet.set_default_row(20)  # 기본 행 높이

        # data start --------------------------------------------- #
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        # title_list
        header_src = [[],
                      ['직급명', 'name', 14],
                      ['승급표준년수', 'promotion_period', 14],
                      ['허용직위', 'positions', 28],
                      ['신입부여기준', 'criteria_new', 32]]
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
        title_format = workbook.add_format()
        title_format.set_bold()
        title_format.set_font_size(18)
        title_format.set_align('vcenter')
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 직급 정보 목록', title_format)

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header - 1
        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

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
        search = request.GET.get('search')
        obj_list = JobGrade.objects.filter(company=company)
        obj_list = obj_list.filter(
            Q(name__icontains=search) |
            Q(promotion_period__icontains=search) |
            Q(positions__name__icontains=search) |
            Q(criteria_new__icontains=search)) if search else obj_list

        base_data = obj_list.values(*params)
        data = []
        for bd in base_data:
            bd['p_list'] = []
            if len(data) == 0:
                bd['p_list'].append(bd['positions'])
                data.append(bd)
            else:
                is_exist = False
                for dt in data:
                    if dt['name'] == bd['name']:
                        is_exist = True
                        dt['p_list'].append(bd['positions'])
                if not is_exist:
                    bd['p_list'].append(bd['positions'])
                    data.append(bd)

        for i, dt in enumerate(data):
            dt['num'] = i + 1
            dt['positions'] = dt['p_list']
            del dt['p_list']

        b_format = workbook.add_format()
        b_format.set_border()
        b_format.set_align('center')
        b_format.set_align('vcenter')
        b_format.set_num_format('yyyy-mm-dd')

        body_format = {
            'border': True,
            'valign': 'vcenter',
            'num_format': '#,##0'
        }

        # Turn off some of the warnings:
        worksheet.ignore_errors({'number_stored_as_text': 'A:D'})

        def get_position(pk):
            return Position.objects.get(pk=pk).name

        # Write body
        for i, row in enumerate(data):
            row_num += 1
            row_data = [row['num'], row['name'], row['promotion_period'], row['positions'], row['criteria_new']]

            for col_num, cell_data in enumerate(row_data):
                if type(cell_data) == list:
                    positions = [get_position(i) for i in cell_data]
                    cell_data = ', '.join(sorted(positions))
                if col_num in (3, 4):
                    body_format['align'] = 'left'
                else:
                    body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)
        # data finish -------------------------------------------- #

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = f'{TODAY}-grades.xlsx'
        file_format = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = HttpResponse(output, content_type=file_format)
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response


class ExportExamples(View):
    """Examples"""

    @staticmethod
    def get(request):
        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()

        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('시트 타이틀')

        worksheet.set_default_row(20)  # 기본 행 높이

        # data start --------------------------------------------- #
        project = Project.objects.get(pk=request.GET.get('project'))

        # title_list
        header_src = [[],
                      ['head title', 'column', 10]]
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
        title_format = workbook.add_format()
        title_format.set_bold()
        title_format.set_font_size(18)
        title_format.set_align('vcenter')
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, '시트 헤더 타이틀', title_format)

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header - 1
        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

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
        obj_list = Contract.objects.filter(project=project)

        data = obj_list.values_list(*params)

        b_format = workbook.add_format()
        b_format.set_border()
        b_format.set_align('center')
        b_format.set_align('vcenter')
        b_format.set_num_format('yyyy-mm-dd')

        body_format = {
            'border': True,
            'valign': 'vcenter',
            'num_format': '#,##0'
        }

        # Turn off some of the warnings:
        # worksheet.ignore_errors({'number_stored_as_text': 'F:G'})

        # Write body
        for i, row in enumerate(data):
            row = list(row)
            row_num += 1
            row.insert(0, i + 1)
            for col_num, cell_data in enumerate(row):
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)

        # data finish -------------------------------------------- #

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = f'{TODAY}-file_title.xlsx'
        file_format = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = HttpResponse(output, content_type=file_format)
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response
