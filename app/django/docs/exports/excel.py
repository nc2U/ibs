import datetime

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from _excel.mixins import ExcelExportMixin
from company.models import Company
from docs.courts import COURT_CHOICES
from docs.models import LawsuitCase
from project.models import Project

TODAY = datetime.date.today().strftime('%Y-%m-%d')


class ExportSuitCases(ExcelExportMixin):
    """프로젝트 소송 사건 목록"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('소송_목록')

        # data start --------------------------------------------- #
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return HttpResponse('인증이 필요합니다.', status=401)

        is_admin = user.is_superuser or getattr(user, 'work_manager', False)
        from work.models.project import IssueProject

        com_id = request.GET.get('company')
        company = None
        if com_id:
            try:
                company = Company.objects.get(pk=com_id)
            except (Company.DoesNotExist, ValueError):
                return HttpResponse('존재하지 않는 회사입니다.', status=404)

        proj_id = request.GET.get('project')
        project = None
        if proj_id:
            try:
                project = Project.objects.get(pk=proj_id)
            except (Project.DoesNotExist, ValueError):
                return HttpResponse('존재하지 않는 프로젝트입니다.', status=404)

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)

        # 사전 포맷 생성 (루프 내 중복 생성 방지)
        center_format = workbook.add_format({
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0'
        })
        date_format = workbook.add_format({
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': 'yyyy-mm-dd'
        })
        left_format = workbook.add_format({
            'border': True,
            'align': 'left',
            'valign': 'vcenter',
            'num_format': '#,##0'
        })

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
        if is_admin:
            obj_list = LawsuitCase.objects.all()
        else:
            accessible_projects = IssueProject.objects.filter(members__user=user)
            obj_list = LawsuitCase.objects.filter(issue_project__in=accessible_projects)

        if company:
            obj_list = obj_list.filter(issue_project__company=company)

        is_real_dev = request.GET.get('is_real_dev')
        sort = request.GET.get('sort')
        level = request.GET.get('level')
        court = request.GET.get('court')
        in_progress = request.GET.get('in_progress')

        obj_list = obj_list.filter(issue_project__project__isnull=True) if is_real_dev == 'false' else obj_list
        obj_list = obj_list.filter(issue_project__project=project) if project and is_real_dev == 'true' else obj_list
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

        data = list(obj_list.values_list(*params))

        # 관련 사건(related_case) ID 수집 및 사전 맵핑 (N+1 쿼리 제거)
        # params index 2 = 'related_case'
        related_case_ids = [row[2] for row in data if row[2]]
        related_dict = (
            dict(LawsuitCase.objects.filter(id__in=related_case_ids).values_list('id', 'case_number'))
            if related_case_ids else {}
        )

        sort_dict = dict(LawsuitCase.SORT_CHOICES)
        level_dict = dict(LawsuitCase.LEVEL_CHOICES)
        court_dict = dict(COURT_CHOICES)

        # Write body
        for i, row in enumerate(data):
            row = list(row)
            row_num += 1
            row.insert(0, i + 1)
            for col_num, cell_data in enumerate(row):
                if col_num == 1:
                    cell_data = sort_dict.get(cell_data, cell_data or '')
                elif col_num == 2:
                    cell_data = level_dict.get(cell_data, cell_data or '')
                elif col_num == 3:
                    cell_data = related_dict.get(cell_data, '') if cell_data else ''
                elif col_num == 5:
                    cell_data = court_dict.get(cell_data, cell_data or '') if cell_data else ''

                if col_num in (15, 16):
                    bformat = date_format
                elif col_num < 6:
                    bformat = center_format
                else:
                    bformat = left_format
                worksheet.write(row_num, col_num, cell_data, bformat)

        # data finish -------------------------------------------- #

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = request.GET.get('filename') or 'lawsuit_cases'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)


class ExportSuitCase(ExcelExportMixin):
    """프로젝트 소송 사건 디테일"""

    def get(self, request):
        # 워크북 생성
        output, workbook, worksheet = self.create_workbook('소송_사건', False, 25)

        # data start --------------------------------------------- #
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return HttpResponse('인증이 필요합니다.', status=401)

        is_admin = user.is_superuser or getattr(user, 'work_manager', False)
        obj = get_object_or_404(LawsuitCase, pk=request.GET.get('pk'))

        # RLS 권한 제어: 관리자가 아닌 경우 해당 사건의 워크스페이스 멤버십 확인
        if not is_admin:
            from work.models.project import IssueProject
            if not IssueProject.objects.filter(pk=obj.issue_project_id, members__user=user).exists():
                return HttpResponse('해당 소송 사건을 열람할 권한이 없습니다.', status=403)

        # 포맷 생성
        title_format = self.create_title_format(workbook)
        h_format = self.create_header_format(workbook)
        center_format = self.create_center_format(workbook)
        num_format = self.create_number_format(workbook)

        # 1. Title
        row_num = 0
        worksheet.set_row(row_num, 50)
        worksheet.merge_range(row_num, 0, row_num, 3, str(obj), title_format)

        # 3. Header - 1
        row_num = 1
        worksheet.set_row(row_num, 20, workbook.add_format({'bold': True}))

        # Adjust the column width.
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 50)
        worksheet.set_column(2, 2, 20)
        worksheet.set_column(3, 3, 50)

        # 4. Body

        # Turn off the warnings:
        worksheet.ignore_errors({'number_stored_as_text': 'B:D'})

        # table header
        row_num = 2
        worksheet.write(row_num, 0, '구분', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3, '내용', h_format)

        row_num = 3
        worksheet.write(row_num, 0, '사건 번호', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3, str(obj.case_number), center_format)

        row_num = 4
        worksheet.write(row_num, 0, '사건명', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3, str(obj.case_name), center_format)

        row_num = 5
        worksheet.write(row_num, 0, '유형', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3, obj.get_sort_display() or '', center_format)

        row_num = 6
        worksheet.write(row_num, 0, '심급', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3, obj.get_level_display() or '', center_format)

        row_num = 7
        worksheet.write(row_num, 0, '관련 사건', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3, str(obj.related_case or ''), center_format)

        row_num = 8
        worksheet.write(row_num, 0, '관할 법원', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3, obj.get_court_display() or '', center_format)

        row_num = 9
        worksheet.write(row_num, 0, '처리기관', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3, str(obj.other_agency), center_format)

        row_num = 10
        worksheet.write(row_num, 0, '원고(채권자)', h_format)
        worksheet.write(row_num, 1, str(obj.plaintiff), center_format)
        worksheet.write(row_num, 2, '피고(채무자)', h_format)
        worksheet.write(row_num, 3, str(obj.defendant), center_format)

        row_num = 11
        worksheet.write(row_num, 0, '원고측 대리인', h_format)
        worksheet.write(row_num, 1, str(obj.plaintiff_attorney), center_format)
        worksheet.write(row_num, 2, '피고측 대리인', h_format)
        worksheet.write(row_num, 3, str(obj.defendant_attorney), center_format)

        row_num = 12
        worksheet.write(row_num, 0, '원고 소가', h_format)
        worksheet.write(row_num, 1, obj.plaintiff_case_price, num_format)
        worksheet.write(row_num, 2, '피고 소가', h_format)
        worksheet.write(row_num, 3, obj.defendant_case_price, num_format)

        row_num = 13
        worksheet.write(row_num, 0, '제3채무자', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3, str(obj.related_debtor), center_format)

        row_num = 14
        worksheet.write(row_num, 0, '사건개시일', h_format)
        worksheet.write(row_num, 1, str(obj.case_start_date), center_format)
        worksheet.write(row_num, 2, '사건종결일', h_format)
        worksheet.write(row_num, 3, str(obj.case_end_date) if obj.case_end_date else '', center_format)

        row_num = 15
        worksheet.write(row_num, 0, '개요 및 경과', h_format)
        worksheet.merge_range(row_num, 1, row_num, 3, str(obj.summary), center_format)

        # data finish -------------------------------------------- #

        # Close the workbook before sending the data.
        workbook.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        filename = request.GET.get('filename') or 'lawsuit_case'
        filename = f'{filename}-{TODAY}'
        return self.create_response(output, workbook, filename)
