"""
Company Excel Export Views

회사 관련 Excel 내보내기 뷰들
"""
import datetime
import json

from django.core import serializers
from django.db.models import Q

from _excel.mixins import ExcelExportMixin
from company.models import (Company, Staff, Department, JobGrade, Position, DutyTitle,
                            ExecutiveRank, Executive, PersonnelOrder, StaffCareer, StaffCertificate,
                            StaffRewardPunishment, StaffLeaveQuota, StaffLeaveUsage, StaffEvaluation,
                            PromotionCandidate)
from contract.models import Contract
from project.models import Project

TODAY = datetime.date.today().strftime('%Y-%m-%d')


class ExportStaffs(ExcelExportMixin):
    """직원 목록 정보"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('직원_정보')

        # data start --------------------------------------------- #
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

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
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 직원 정보 목록', title_format)

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
        obj_list = Staff.objects.filter(company=company).prefetch_related(
            'assignments__department', 'assignments__position', 'assignments__duty'
        )

        # get query list
        sort = request.GET.get('sort')
        department = request.GET.get('department')
        grade = request.GET.get('grade')
        position = request.GET.get('position')
        duty = request.GET.get('duty')
        status = request.GET.get('status')
        search = request.GET.get('search')

        obj_list = obj_list.filter(sort=sort) if sort else obj_list
        obj_list = obj_list.filter(assignments__department_id=department) if department else obj_list
        obj_list = obj_list.filter(grade_id=grade) if grade else obj_list
        obj_list = obj_list.filter(assignments__position_id=position) if position else obj_list
        obj_list = obj_list.filter(assignments__duty_id=duty) if duty else obj_list
        obj_list = obj_list.filter(status=status) if status else obj_list
        obj_list = obj_list.filter(
            Q(name__icontains=search) |
            Q(id_number__icontains=search) |
            Q(personal_phone__icontains=search) |
            Q(email__icontains=search)).distinct() if search else obj_list

        body_format = {
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': 'yyyy-mm-dd'
        }

        # Turn off some of the warnings:
        worksheet.ignore_errors({'number_stored_as_text': 'B:L'})

        # Write body
        sort_map = dict(Staff.SORT_CHOICES)
        status_map = dict(Staff.STATUS_CHOICES)
        for i, s in enumerate(obj_list):
            row_num += 1
            row_data = [
                i + 1,
                sort_map.get(s.sort, s.sort),
                s.name,
                s.id_number,
                s.personal_phone,
                s.email or '',
                s.department.name if s.department else '',
                s.grade.name if s.grade else '',
                s.position.name if s.position else '',
                s.duty.name if s.duty else '',
                s.date_join,
                status_map.get(s.status, s.status),
                s.date_leave or '',
            ]
            for col_num, cell_data in enumerate(row_data):
                if col_num in (10, 12):
                    body_format['num_format'] = 'yyyy-mm-dd'
                else:
                    body_format['num_format'] = '@'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)

        # data finish -------------------------------------------- #

        # Close the workbook before sending the data.
        filename = request.GET.get('filename') or 'staffs'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportDeparts(ExcelExportMixin):
    """부서 목록 정보"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('부서_정보')

        # data start --------------------------------------------- #
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

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
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 부서 정보 목록', title_format)

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
        upper_depart = request.GET.get('upper_depart')
        search = request.GET.get('search')
        obj_list = Department.objects.filter(company=company)

        obj_list = obj_list.filter(upper_depart_id=upper_depart) if upper_depart else obj_list
        obj_list = obj_list.filter(
            Q(name__icontains=search) |
            Q(task__icontains=search)) if search else obj_list

        data = obj_list.values_list(*params)

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
        filename = request.GET.get('filename') or 'departs'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportPositions(ExcelExportMixin):
    """직위 목록 정보"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('직위_정보')

        # data start --------------------------------------------- #
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

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
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 직위 정보 목록', title_format)

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
        search = request.GET.get('search')
        obj_list = Position.objects.filter(company=company)
        obj_list = obj_list.filter(name__icontains=search) if search else obj_list

        json_data = serializers.serialize('json', obj_list)
        data = [i['fields'] for i in json.loads(json_data)]
        # data = obj_list.values_list(*params)

        body_format = {
            'border': True,
            'valign': 'vcenter',
            'num_format': '#,##0'
        }

        # Turn off some of the warnings:
        worksheet.ignore_errors({'number_stored_as_text': 'A:D'})

        def get_grade(pk):
            return JobGrade.objects.get(pk=pk).code

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
        filename = request.GET.get('filename') or 'positions'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportDuties(ExcelExportMixin):
    """직책 정보 목록"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('직책_정보')

        # data start --------------------------------------------- #
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

        # title_list
        header_src = [[],
                      ['코드', 'code', 15],
                      ['직책명', 'name', 20],
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
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 직책 정보 목록', title_format)

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
        search = request.GET.get('search')
        obj_list = DutyTitle.objects.filter(company=company)
        obj_list = obj_list.filter(
            Q(code__icontains=search) | Q(name__icontains=search) | Q(desc__icontains=search)
        ) if search else obj_list

        data = obj_list.values_list(*params)

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
                if col_num in (2, 3):
                    body_format['align'] = 'left'
                else:
                    body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)
        # data finish -------------------------------------------- #

        # Close the workbook before sending the data.
        filename = request.GET.get('filename') or 'duties'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportGrades(ExcelExportMixin):
    """직급 정보 목록"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('직급_정보')

        # data start --------------------------------------------- #
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

        # title_list
        header_src = [[],
                      ['코드', 'code', 10],
                      ['역할', 'role', 20],
                      ['최소체류기간(년)', 'min_promotion_years', 16],
                      ['허용직위', 'positions', 28],
                      ['승급기준', 'promotion_criteria', 32]]
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
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 직급 정보 목록', title_format)

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
        search = request.GET.get('search')
        obj_list = JobGrade.objects.filter(company=company)
        obj_list = obj_list.filter(
            Q(code__icontains=search) |
            Q(name__icontains=search) |
            Q(role__icontains=search) |
            Q(min_promotion_years__icontains=search) |
            Q(positions__name__icontains=search) |
            Q(promotion_criteria__icontains=search)) if search else obj_list

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
                    if dt['code'] == bd['code']:
                        is_exist = True
                        dt['p_list'].append(bd['positions'])
                if not is_exist:
                    bd['p_list'].append(bd['positions'])
                    data.append(bd)

        for i, dt in enumerate(data):
            dt['num'] = i + 1
            dt['positions'] = dt['p_list']
            del dt['p_list']

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
            row_data = [row['num'], row['code'], row['role'], row['min_promotion_years'], row['positions'],
                        row['promotion_criteria']]

            for col_num, cell_data in enumerate(row_data):
                if type(cell_data) == list:
                    positions = [get_position(i) for i in cell_data]
                    cell_data = ', '.join(sorted(positions))
                if col_num in (2, 4, 5):
                    body_format['align'] = 'left'
                else:
                    body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)
        # data finish -------------------------------------------- #

        # Close the workbook before sending the data.
        filename = request.GET.get('filename') or 'grades'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportExecutiveRanks(ExcelExportMixin):
    """임원 직위 목록"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('임원_직위_정보')

        # data start --------------------------------------------- #
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

        # title_list
        header_src = [[],
                      ['서열 순서', 'rank_order', 12],
                      ['직위 코드', 'code', 15],
                      ['임원 직위명', 'name', 20],
                      ['역할/관장 설명', 'role_desc', 45]]
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
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 임원 직위 정보 목록', title_format)

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
        search = request.GET.get('search')
        obj_list = ExecutiveRank.objects.filter(company=company)
        obj_list = obj_list.filter(
            Q(code__icontains=search) | Q(name__icontains=search) | Q(role_desc__icontains=search)
        ) if search else obj_list

        data = obj_list.values_list(*params)

        body_format = {
            'border': True,
            'valign': 'vcenter',
            'num_format': '#,##0'
        }

        # Write body
        for i, row in enumerate(data):
            row = list(row)
            row_num += 1
            row.insert(0, i + 1)
            for col_num, cell_data in enumerate(row):
                if col_num in (3, 4):
                    body_format['align'] = 'left'
                else:
                    body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)
        # data finish -------------------------------------------- #

        # Close the workbook before sending the data.
        filename = request.GET.get('filename') or 'executive-ranks'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportExecutives(ExcelExportMixin):
    """임원 재임/등기 정보 목록"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('임원_재임_정보')

        # data start --------------------------------------------- #
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

        # title_list
        header_src = [[],
                      ['성명', 'staff__name', 12],
                      ['임원 직위', 'rank__name', 13],
                      ['상법상 지위', 'director_type', 15],
                      ['등기 여부', 'is_registered', 10],
                      ['상근 여부', 'is_standing', 10],
                      ['대표권 구분', 'represent_type', 12],
                      ['취임일(임기시작)', 'term_start', 15],
                      ['임기만료일', 'term_end', 15],
                      ['최초선임일', 'appointed_date', 15],
                      ['비고', 'note', 25]]
        titles = ['No']  # header titles
        widths = [7]  # No. 컬럼 넓이

        for el in header_src:
            if el:
                titles.append(el[0])
                widths.append(el[2])

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 임원 재임 정보 목록', title_format)

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
        obj_list = Executive.objects.filter(company=company).select_related('staff', 'rank')

        rank = request.GET.get('rank')
        director_type = request.GET.get('director_type')
        is_registered = request.GET.get('is_registered')
        is_standing = request.GET.get('is_standing')
        represent_type = request.GET.get('represent_type')
        search = request.GET.get('search')

        if rank:
            obj_list = obj_list.filter(rank_id=rank)
        if director_type:
            obj_list = obj_list.filter(director_type=director_type)
        if is_registered in ('true', 'True', '1', True):
            obj_list = obj_list.filter(is_registered=True)
        elif is_registered in ('false', 'False', '0', False):
            obj_list = obj_list.filter(is_registered=False)
        if is_standing in ('true', 'True', '1', True):
            obj_list = obj_list.filter(is_standing=True)
        elif is_standing in ('false', 'False', '0', False):
            obj_list = obj_list.filter(is_standing=False)
        if represent_type:
            obj_list = obj_list.filter(represent_type=represent_type)
        if search:
            obj_list = obj_list.filter(
                Q(staff__name__icontains=search) |
                Q(rank__name__icontains=search) |
                Q(note__icontains=search)
            )

        body_format = {
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '@'
        }

        director_map = dict(Executive.DIRECTOR_CHOICES)
        represent_map = dict(Executive.REPRESENT_CHOICES)

        for i, exec_item in enumerate(obj_list):
            row_num += 1
            row_data = [
                i + 1,
                exec_item.staff.name if exec_item.staff else '',
                exec_item.rank.name if exec_item.rank else '',
                director_map.get(exec_item.director_type, exec_item.director_type),
                '등기' if exec_item.is_registered else '비등기',
                '상근' if exec_item.is_standing else '비상근',
                represent_map.get(exec_item.represent_type, exec_item.represent_type),
                exec_item.term_start or '',
                exec_item.term_end or '',
                exec_item.appointed_date or '',
                exec_item.note or '',
            ]

            for col_num, cell_data in enumerate(row_data):
                if col_num in (7, 8, 9) and cell_data:
                    body_format['num_format'] = 'yyyy-mm-dd'
                else:
                    body_format['num_format'] = '@'
                if col_num == 10:
                    body_format['align'] = 'left'
                else:
                    body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)

        # data finish -------------------------------------------- #
        filename = request.GET.get('filename') or 'executives'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportAppointments(ExcelExportMixin):
    """인사 발령 이력 목록"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('인사_발령_이력')

        # data start --------------------------------------------- #
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

        # title_list
        header_src = [[],
                      ['발령일자', 'order_date', 13],
                      ['발령구분', 'order_type', 13],
                      ['문서번호', 'order_no', 15],
                      ['대상직원', 'staff__name', 12],
                      ['발령전 부서', 'prev_department__name', 14],
                      ['발령전 직위', 'prev_position__name', 13],
                      ['발령전 직책', 'prev_duty__name', 13],
                      ['발령후 부서', 'new_department__name', 14],
                      ['발령후 직위', 'new_position__name', 13],
                      ['발령후 직책', 'new_duty__name', 13],
                      ['발령 사유 및 세부내용', 'description', 30],
                      ['종료예정일', 'effective_end_date', 13]]
        titles = ['No']
        widths = [7]

        for el in header_src:
            if el:
                titles.append(el[0])
                widths.append(el[2])

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 인사 발령 이력 목록', title_format)

        # 2. Pre Header - Date
        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        # 3. Header - 1
        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

        for i, col_width in enumerate(widths):
            worksheet.set_column(i, i, col_width)

        for col_num, title in enumerate(titles):
            worksheet.write(row_num, col_num, title, h_format)

        # 4. Body
        obj_list = PersonnelOrder.objects.filter(company=company).select_related(
            'staff', 'prev_department', 'prev_grade', 'prev_position', 'prev_duty',
            'new_department', 'new_grade', 'new_position', 'new_duty'
        )

        staff = request.GET.get('staff')
        order_type = request.GET.get('order_type')
        department = request.GET.get('department')
        search = request.GET.get('search')

        if staff:
            obj_list = obj_list.filter(staff_id=staff)
        if order_type:
            obj_list = obj_list.filter(order_type=order_type)
        if department:
            obj_list = obj_list.filter(new_department_id=department)
        if search:
            obj_list = obj_list.filter(
                Q(staff__name__icontains=search) |
                Q(order_no__icontains=search) |
                Q(description__icontains=search)
            )

        body_format = {
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '@'
        }

        order_type_map = dict(PersonnelOrder.ORDER_TYPE_CHOICES)

        for i, order in enumerate(obj_list):
            row_num += 1
            row_data = [
                i + 1,
                order.order_date or '',
                order_type_map.get(order.order_type, order.order_type),
                order.order_no or '',
                order.staff.name if order.staff else '',
                order.prev_department.name if order.prev_department else '-',
                order.prev_position.name if order.prev_position else '-',
                order.prev_duty.name if order.prev_duty else '-',
                order.new_department.name if order.new_department else '-',
                order.new_position.name if order.new_position else '-',
                order.new_duty.name if order.new_duty else '-',
                order.description or '',
                order.effective_end_date or '',
            ]

            for col_num, cell_data in enumerate(row_data):
                if col_num in (1, 12) and cell_data:
                    body_format['num_format'] = 'yyyy-mm-dd'
                else:
                    body_format['num_format'] = '@'
                if col_num in (3, 11):
                    body_format['align'] = 'left'
                else:
                    body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)

        # data finish -------------------------------------------- #
        filename = request.GET.get('filename') or 'personnel-orders'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportStaffCareers(ExcelExportMixin):
    """직원 이전 경력 이력 목록"""

    def get(self, request):
        output, workbook, worksheet = self.create_workbook('직원_경력_이력')
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

        header_src = [[],
                      ['대상직원', 'staff__name', 12],
                      ['근무처/기관명', 'company_name', 20],
                      ['부서/조직명', 'department_name', 16],
                      ['직위/직급', 'position_title', 14],
                      ['담당 업무', 'assigned_tasks', 25],
                      ['시작일', 'start_date', 13],
                      ['종료일', 'end_date', 13],
                      ['인정률(%)', 'recognized_ratio', 10],
                      ['비고/퇴사사유', 'note', 25]]
        titles = ['No']
        widths = [7]

        for el in header_src:
            if el:
                titles.append(el[0])
                widths.append(el[2])

        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 직원 경력 사항 목록', title_format)

        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

        for i, col_width in enumerate(widths):
            worksheet.set_column(i, i, col_width)

        for col_num, title in enumerate(titles):
            worksheet.write(row_num, col_num, title, h_format)

        obj_list = StaffCareer.objects.filter(company=company).select_related('staff')
        staff = request.GET.get('staff')
        search = request.GET.get('search')
        if staff:
            obj_list = obj_list.filter(staff_id=staff)
        if search:
            obj_list = obj_list.filter(
                Q(staff__name__icontains=search) |
                Q(company_name__icontains=search) |
                Q(assigned_tasks__icontains=search)
            )

        body_format = {'border': True, 'align': 'center', 'valign': 'vcenter', 'num_format': '@'}

        for i, item in enumerate(obj_list):
            row_num += 1
            row_data = [
                i + 1,
                item.staff.name if item.staff else '',
                item.company_name,
                item.department_name or '',
                item.position_title or '',
                item.assigned_tasks or '',
                item.start_date or '',
                item.end_date or '',
                f'{item.recognized_ratio}%',
                item.note or '',
            ]
            for col_num, cell_data in enumerate(row_data):
                if col_num in (6, 7) and cell_data:
                    body_format['num_format'] = 'yyyy-mm-dd'
                else:
                    body_format['num_format'] = '@'
                if col_num in (2, 5, 9):
                    body_format['align'] = 'left'
                else:
                    body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)

        filename = request.GET.get('filename') or 'staff-careers'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportStaffCertificates(ExcelExportMixin):
    """직원 자격 및 면허 목록"""

    def get(self, request):
        output, workbook, worksheet = self.create_workbook('직원_자격면허')
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

        header_src = [[],
                      ['대상직원', 'staff__name', 12],
                      ['자격/면허명', 'name', 20],
                      ['등급/급수', 'grade', 15],
                      ['자격/등록 번호', 'cert_number', 18],
                      ['발급 기관', 'issuer', 18],
                      ['취득일자', 'acquired_date', 13],
                      ['만료/갱신일자', 'expire_date', 13],
                      ['수당지급', 'has_allowance', 10],
                      ['비고', 'note', 25]]
        titles = ['No']
        widths = [7]

        for el in header_src:
            if el:
                titles.append(el[0])
                widths.append(el[2])

        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 직원 자격/면허 목록', title_format)

        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

        for i, col_width in enumerate(widths):
            worksheet.set_column(i, i, col_width)

        for col_num, title in enumerate(titles):
            worksheet.write(row_num, col_num, title, h_format)

        obj_list = StaffCertificate.objects.filter(company=company).select_related('staff')
        staff = request.GET.get('staff')
        search = request.GET.get('search')
        if staff:
            obj_list = obj_list.filter(staff_id=staff)
        if search:
            obj_list = obj_list.filter(
                Q(staff__name__icontains=search) |
                Q(name__icontains=search) |
                Q(issuer__icontains=search)
            )

        body_format = {'border': True, 'align': 'center', 'valign': 'vcenter', 'num_format': '@'}

        for i, item in enumerate(obj_list):
            row_num += 1
            row_data = [
                i + 1,
                item.staff.name if item.staff else '',
                item.name,
                item.grade or '',
                item.cert_number or '',
                item.issuer or '',
                item.acquired_date or '',
                item.expire_date or '',
                '지급' if item.has_allowance else '미지급',
                item.note or '',
            ]
            for col_num, cell_data in enumerate(row_data):
                if col_num in (6, 7) and cell_data:
                    body_format['num_format'] = 'yyyy-mm-dd'
                else:
                    body_format['num_format'] = '@'
                if col_num in (2, 8):
                    body_format['align'] = 'left'
                else:
                    body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)

        filename = request.GET.get('filename') or 'staff-certificates'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportStaffRewards(ExcelExportMixin):
    """직원 상벌 이력 목록"""

    def get(self, request):
        output, workbook, worksheet = self.create_workbook('직원_상벌이력')
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

        header_src = [[],
                      ['대상직원', 'staff__name', 12],
                      ['구분', 'sort', 10],
                      ['항목명', 'type_name', 18],
                      ['처분/수여일자', 'action_date', 13],
                      ['효력만료일', 'expire_date', 13],
                      ['수여/처분 기관', 'organization', 18],
                      ['사유/근거', 'reason', 30],
                      ['비고', 'note', 20]]
        titles = ['No']
        widths = [7]

        for el in header_src:
            if el:
                titles.append(el[0])
                widths.append(el[2])

        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 직원 상벌 이력 목록', title_format)

        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

        for i, col_width in enumerate(widths):
            worksheet.set_column(i, i, col_width)

        for col_num, title in enumerate(titles):
            worksheet.write(row_num, col_num, title, h_format)

        obj_list = StaffRewardPunishment.objects.filter(company=company).select_related('staff')
        staff = request.GET.get('staff')
        sort = request.GET.get('sort')
        search = request.GET.get('search')
        if staff:
            obj_list = obj_list.filter(staff_id=staff)
        if sort:
            obj_list = obj_list.filter(sort=sort)
        if search:
            obj_list = obj_list.filter(
                Q(staff__name__icontains=search) |
                Q(type_name__icontains=search) |
                Q(reason__icontains=search)
            )

        body_format = {'border': True, 'align': 'center', 'valign': 'vcenter', 'num_format': '@'}

        for i, item in enumerate(obj_list):
            row_num += 1
            row_data = [
                i + 1,
                item.staff.name if item.staff else '',
                item.get_sort_display(),
                item.type_name,
                item.action_date or '',
                item.expire_date or '',
                item.organization or '',
                item.reason or '',
                item.note or '',
            ]
            for col_num, cell_data in enumerate(row_data):
                if col_num in (4, 5) and cell_data:
                    body_format['num_format'] = 'yyyy-mm-dd'
                else:
                    body_format['num_format'] = '@'
                if col_num in (3, 7, 8):
                    body_format['align'] = 'left'
                else:
                    body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)

        filename = request.GET.get('filename') or 'staff-rewards'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportStaffLeaveQuotas(ExcelExportMixin):
    """직원 연차 부여 및 잔여 현황 목록"""

    def get(self, request):
        output, workbook, worksheet = self.create_workbook('연차_부여_잔여')
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

        header_src = [[],
                      ['대상직원', 'staff__name', 12],
                      ['대상연도', 'year', 10],
                      ['기본발생', 'granted_days', 11],
                      ['이월/조정', 'carry_over_days', 11],
                      ['포상/가산', 'reward_days', 11],
                      ['총 부여일수', 'total_granted_days', 12],
                      ['사용일수', 'used_days', 11],
                      ['잔여일수', 'remaining_days', 11],
                      ['사용가능 시작일', 'valid_start', 14],
                      ['사용가능 만료일', 'valid_end', 14],
                      ['비고', 'note', 25]]
        titles = ['No']
        widths = [7]

        for el in header_src:
            if el:
                titles.append(el[0])
                widths.append(el[2])

        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 연차 부여 및 잔여 현황', title_format)

        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

        for i, col_width in enumerate(widths):
            worksheet.set_column(i, i, col_width)

        for col_num, title in enumerate(titles):
            worksheet.write(row_num, col_num, title, h_format)

        obj_list = StaffLeaveQuota.objects.filter(company=company).select_related('staff')
        staff = request.GET.get('staff')
        year = request.GET.get('year')
        search = request.GET.get('search')
        if staff:
            obj_list = obj_list.filter(staff_id=staff)
        if year:
            obj_list = obj_list.filter(year=year)
        if search:
            obj_list = obj_list.filter(
                Q(staff__name__icontains=search) |
                Q(note__icontains=search)
            )

        body_format = {'border': True, 'align': 'center', 'valign': 'vcenter', 'num_format': '#,##0.00'}

        for i, item in enumerate(obj_list):
            row_num += 1
            row_data = [
                i + 1,
                item.staff.name if item.staff else '',
                f'{item.year}년',
                float(item.granted_days or 0),
                float(item.carry_over_days or 0),
                float(item.reward_days or 0),
                float(item.total_granted_days or 0),
                float(item.used_days or 0),
                float(item.remaining_days or 0),
                item.valid_start or '',
                item.valid_end or '',
                item.note or '',
            ]
            for col_num, cell_data in enumerate(row_data):
                if col_num in (3, 4, 5, 6, 7, 8):
                    body_format['num_format'] = '#,##0.00'
                    body_format['align'] = 'right'
                elif col_num in (9, 10) and cell_data:
                    body_format['num_format'] = 'yyyy-mm-dd'
                    body_format['align'] = 'center'
                elif col_num == 11:
                    body_format['num_format'] = '@'
                    body_format['align'] = 'left'
                else:
                    body_format['num_format'] = '@'
                    body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)

        filename = request.GET.get('filename') or 'staff-leave-quotas'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportStaffLeaveUsages(ExcelExportMixin):
    """직원 휴가/연차 사용 내역 목록"""

    def get(self, request):
        output, workbook, worksheet = self.create_workbook('휴가_사용_내역')
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

        header_src = [[],
                      ['대상직원', 'staff__name', 12],
                      ['휴가구분', 'leave_type', 14],
                      ['시작일', 'start_date', 13],
                      ['종료일', 'end_date', 13],
                      ['차감일수', 'deduction_days', 11],
                      ['휴가사유', 'reason', 25],
                      ['취소여부', 'is_cancelled', 10],
                      ['신청/등록일', 'created', 14]]
        titles = ['No']
        widths = [7]

        for el in header_src:
            if el:
                titles.append(el[0])
                widths.append(el[2])

        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 휴가 사용 내역', title_format)

        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

        for i, col_width in enumerate(widths):
            worksheet.set_column(i, i, col_width)

        for col_num, title in enumerate(titles):
            worksheet.write(row_num, col_num, title, h_format)

        obj_list = StaffLeaveUsage.objects.filter(company=company).select_related('staff')
        staff = request.GET.get('staff')
        leave_type = request.GET.get('leave_type')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        search = request.GET.get('search')

        if staff:
            obj_list = obj_list.filter(staff_id=staff)
        if leave_type:
            obj_list = obj_list.filter(leave_type=leave_type)
        if start_date:
            obj_list = obj_list.filter(start_date__gte=start_date)
        if end_date:
            obj_list = obj_list.filter(end_date__lte=end_date)
        if search:
            obj_list = obj_list.filter(
                Q(staff__name__icontains=search) |
                Q(reason__icontains=search)
            )

        body_format = {'border': True, 'align': 'center', 'valign': 'vcenter', 'num_format': '@'}

        for i, item in enumerate(obj_list):
            row_num += 1
            cancel_str = '취소됨' if item.is_cancelled else '정상'
            row_data = [
                i + 1,
                item.staff.name if item.staff else '',
                item.get_leave_type_display(),
                item.start_date.strftime('%Y-%m-%d') if item.start_date else '',
                item.end_date.strftime('%Y-%m-%d') if item.end_date else '',
                float(item.deduction_days or 0),
                item.reason or '',
                cancel_str,
                item.created.strftime('%Y-%m-%d') if item.created else '',
            ]
            for col_num, cell_data in enumerate(row_data):
                if col_num == 5:
                    body_format['num_format'] = '#,##0.00'
                    body_format['align'] = 'right'
                elif col_num in (3, 4, 8):
                    body_format['num_format'] = 'yyyy-mm-dd'
                    body_format['align'] = 'center'
                elif col_num == 6:
                    body_format['num_format'] = '@'
                    body_format['align'] = 'left'
                else:
                    body_format['num_format'] = '@'
                    body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)

        filename = request.GET.get('filename') or 'staff-leave-usages'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportStaffAttendanceStatus(ExcelExportMixin):
    """직원 연차 및 근태 현황 종합 목록"""

    def get(self, request):
        output, workbook, worksheet = self.create_workbook('근태_현황_종합')
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')
        year = int(request.GET.get('year') or datetime.date.today().year)

        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

        header_src = [[],
                      ['부서', 'department', 14],
                      ['직급/직위', 'position', 12],
                      ['성명', 'name', 12],
                      ['입사일', 'date_join', 12],
                      ['총 부여일수', 'total_granted_days', 12],
                      ['사용일수', 'used_days', 11],
                      ['잔여일수', 'remaining_days', 11],
                      ['연차 사용률', 'usage_rate', 12],
                      ['상태', 'status', 10]]
        titles = ['No']
        widths = [7]

        for el in header_src:
            if el:
                titles.append(el[0])
                widths.append(el[2])

        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, f'{com_name} {year}년도 연차 및 근태 종합 현황', title_format)

        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

        for i, col_width in enumerate(widths):
            worksheet.set_column(i, i, col_width)

        for col_num, title in enumerate(titles):
            worksheet.write(row_num, col_num, title, h_format)

        staff_list = Staff.objects.filter(company=company).select_related('department', 'position', 'grade')
        department = request.GET.get('department')
        status = request.GET.get('status')
        search = request.GET.get('search')

        if department:
            staff_list = staff_list.filter(department_id=department)
        if status:
            staff_list = staff_list.filter(status=status)
        if search:
            staff_list = staff_list.filter(Q(name__icontains=search) | Q(personal_phone__icontains=search))

        body_format = {'border': True, 'align': 'center', 'valign': 'vcenter', 'num_format': '@'}

        for i, s in enumerate(staff_list):
            quota = StaffLeaveQuota.objects.filter(company=company, staff=s, year=year).first()
            tot = float(quota.total_granted_days) if quota else 0.0
            used = float(quota.used_days) if quota else 0.0
            rem = float(quota.remaining_days) if quota else 0.0
            rate_str = f'{(used / tot * 100):.1f}%' if tot > 0 else '0.0%'

            row_num += 1
            row_data = [
                i + 1,
                s.department.name if s.department else '-',
                s.position.name if s.position else (s.grade.code if s.grade else '-'),
                s.name,
                s.date_join.strftime('%Y-%m-%d') if s.date_join else '-',
                tot,
                used,
                rem,
                rate_str,
                s.get_status_display(),
            ]
            for col_num, cell_data in enumerate(row_data):
                if col_num in (5, 6, 7):
                    body_format['num_format'] = '#,##0.00'
                    body_format['align'] = 'right'
                elif col_num == 8:
                    body_format['num_format'] = '@'
                    body_format['align'] = 'right'
                elif col_num == 4:
                    body_format['num_format'] = 'yyyy-mm-dd'
                    body_format['align'] = 'center'
                else:
                    body_format['num_format'] = '@'
                    body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)

        filename = request.GET.get('filename') or 'staff-attendance-status'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportStaffEvaluations(ExcelExportMixin):
    """직원 인사/업적 평가 목록"""

    def get(self, request):
        output, workbook, worksheet = self.create_workbook('인사_평가_목록')
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

        header_src = [[],
                      ['평가연도', 'eval_year', 10],
                      ['평가주기', 'eval_period', 10],
                      ['피평가자', 'staff__name', 12],
                      ['부서', 'staff__department__name', 14],
                      ['직급/직위', 'staff__position__name', 12],
                      ['평가등급', 'grade', 10],
                      ['환산점수', 'score', 11],
                      ['1차 평가자', 'evaluator__name', 12],
                      ['2차 확인자', 'reviewer__name', 12],
                      ['주요 업적 요약', 'achievement_summary', 30],
                      ['종합의견', 'notes', 25]]
        titles = ['No']
        widths = [7]

        for el in header_src:
            if el:
                titles.append(el[0])
                widths.append(el[2])

        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 임직원 인사/업적 평가 목록', title_format)

        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

        for i, col_width in enumerate(widths):
            worksheet.set_column(i, i, col_width)

        for col_num, title in enumerate(titles):
            worksheet.write(row_num, col_num, title, h_format)

        obj_list = StaffEvaluation.objects.filter(company=company).select_related(
            'staff', 'staff__department', 'staff__position', 'staff__grade', 'evaluator', 'reviewer'
        )
        eval_year = request.GET.get('eval_year')
        eval_period = request.GET.get('eval_period')
        grade = request.GET.get('grade')
        staff = request.GET.get('staff')
        search = request.GET.get('search')

        if eval_year:
            obj_list = obj_list.filter(eval_year=eval_year)
        if eval_period:
            obj_list = obj_list.filter(eval_period=eval_period)
        if grade:
            obj_list = obj_list.filter(grade=grade)
        if staff:
            obj_list = obj_list.filter(staff_id=staff)
        if search:
            obj_list = obj_list.filter(
                Q(staff__name__icontains=search) |
                Q(achievement_summary__icontains=search) |
                Q(notes__icontains=search)
            )

        body_format = {'border': True, 'align': 'center', 'valign': 'vcenter', 'num_format': '@'}

        for i, item in enumerate(obj_list):
            row_num += 1
            pos_title = item.staff.position.name if (item.staff and item.staff.position) else (item.staff.grade.code if (item.staff and item.staff.grade) else '-')
            dept_title = item.staff.department.name if (item.staff and item.staff.department) else '-'
            row_data = [
                i + 1,
                f'{item.eval_year}년',
                item.get_eval_period_display(),
                item.staff.name if item.staff else '',
                dept_title,
                pos_title,
                item.grade,
                float(item.score) if item.score is not None else '',
                item.evaluator.name if item.evaluator else '-',
                item.reviewer.name if item.reviewer else '-',
                item.achievement_summary or '',
                item.notes or '',
            ]
            for col_num, cell_data in enumerate(row_data):
                if col_num == 7 and cell_data != '':
                    body_format['num_format'] = '#,##0.00'
                    body_format['align'] = 'right'
                elif col_num in (10, 11):
                    body_format['num_format'] = '@'
                    body_format['align'] = 'left'
                else:
                    body_format['num_format'] = '@'
                    body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)

        filename = request.GET.get('filename') or 'staff-evaluations'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportPromotionCandidates(ExcelExportMixin):
    """승급 심사 대상 및 발령 목록"""

    def get(self, request):
        output, workbook, worksheet = self.create_workbook('승급_심사_목록')
        company = Company.objects.get(pk=request.GET.get('company'))
        com_name = company.name.replace('주식회사 ', '(주)')

        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

        header_src = [[],
                      ['심사연도', 'eval_year', 10],
                      ['대상직원', 'staff__name', 12],
                      ['부서', 'staff__department__name', 14],
                      ['현재직급', 'policy__current_grade__code', 12],
                      ['승급대상직급', 'policy__target_grade__code', 12],
                      ['현직급 체류년수', 'tenure_years', 14],
                      ['평가 평균점수', 'avg_eval_score', 13],
                      ['심사상태', 'status', 12],
                      ['승진발령일', 'promoted_date', 13],
                      ['인사위원회 심의의견', 'committee_review', 30]]
        titles = ['No']
        widths = [7]

        for el in header_src:
            if el:
                titles.append(el[0])
                widths.append(el[2])

        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, com_name + ' 승급 심사 대상 및 발령 목록', title_format)

        row_num = 1
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, len(header_src) - 1, TODAY + ' 현재', workbook.add_format({'align': 'right'}))

        row_num = 2
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

        for i, col_width in enumerate(widths):
            worksheet.set_column(i, i, col_width)

        for col_num, title in enumerate(titles):
            worksheet.write(row_num, col_num, title, h_format)

        obj_list = PromotionCandidate.objects.filter(company=company).select_related(
            'staff', 'staff__department', 'policy', 'policy__current_grade', 'policy__target_grade'
        )
        eval_year = request.GET.get('eval_year')
        status = request.GET.get('status')
        staff = request.GET.get('staff')
        search = request.GET.get('search')

        if eval_year:
            obj_list = obj_list.filter(eval_year=eval_year)
        if status:
            obj_list = obj_list.filter(status=status)
        if staff:
            obj_list = obj_list.filter(staff_id=staff)
        if search:
            obj_list = obj_list.filter(
                Q(staff__name__icontains=search) |
                Q(committee_review__icontains=search)
            )

        body_format = {'border': True, 'align': 'center', 'valign': 'vcenter', 'num_format': '@'}

        for i, item in enumerate(obj_list):
            row_num += 1
            dept_title = item.staff.department.name if (item.staff and item.staff.department) else '-'
            current_g = item.policy.current_grade.code if (item.policy and item.policy.current_grade) else '-'
            target_g = item.policy.target_grade.code if (item.policy and item.policy.target_grade) else '-'
            row_data = [
                i + 1,
                f'{item.eval_year}년',
                item.staff.name if item.staff else '',
                dept_title,
                current_g,
                target_g,
                float(item.tenure_years or 0),
                float(item.avg_eval_score) if item.avg_eval_score is not None else '',
                item.get_status_display(),
                item.promoted_date.strftime('%Y-%m-%d') if item.promoted_date else '-',
                item.committee_review or '',
            ]
            for col_num, cell_data in enumerate(row_data):
                if col_num in (6, 7) and cell_data != '':
                    body_format['num_format'] = '#,##0.0'
                    body_format['align'] = 'right'
                elif col_num == 9 and cell_data != '-':
                    body_format['num_format'] = 'yyyy-mm-dd'
                    body_format['align'] = 'center'
                elif col_num == 10:
                    body_format['num_format'] = '@'
                    body_format['align'] = 'left'
                else:
                    body_format['num_format'] = '@'
                    body_format['align'] = 'center'
                bformat = workbook.add_format(body_format)
                worksheet.write(row_num, col_num, cell_data, bformat)

        filename = request.GET.get('filename') or 'promotion-candidates'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportExamples(ExcelExportMixin):
    """Examples"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('시트_타이틀')

        # data start --------------------------------------------- #
        project = Project.objects.get(pk=request.GET.get('project'))

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

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
        worksheet.merge_range(row_num, 0, row_num, len(header_src) - 1, '시트 헤더 타이틀', title_format)

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
        obj_list = Contract.objects.filter(project=project)

        data = obj_list.values_list(*params)

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
        filename = request.GET.get('filename') or 'examples'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)
