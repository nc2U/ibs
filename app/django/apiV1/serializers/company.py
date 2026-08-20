from rest_framework import serializers

from company.models import Company, Logo, Department, JobGrade, Position, DutyTitle, Staff, StaffAssignment
from work.models.project import IssueProject


# Company --------------------------------------------------------------------------
class DepartsInCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('pk', 'upper_depart', 'name', 'task')


class GradesInCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobGrade
        fields = ('pk', 'code', 'role', 'min_promotion_years', 'promotion_criteria')


class CompanySerializer(serializers.ModelSerializer):
    departments = DepartsInCompanySerializer(many=True, read_only=True)
    grades = GradesInCompanySerializer(many=True, read_only=True)
    com_issue_project = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Company
        fields = ('pk', 'name', 'ceo', 'tax_number', 'org_number', 'business_cond',
                  'business_even', 'es_date', 'op_date', 'zipcode', 'address1',
                  'address2', 'address3', 'departments', 'grades', 'com_issue_project',
                  'is_default')

    @staticmethod
    def get_com_issue_project(obj):
        issue_project = IssueProject.objects.filter(company=obj, type='1').first()
        return issue_project.pk if issue_project else None


class LogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Logo
        fields = ('pk', 'company', 'generic_logo', 'dark_logo', 'simple_logo')


class StaffsInDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ('pk', 'grade', 'name')


class DepartmentSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    manager_name = serializers.CharField(source='manager.name', read_only=True, allow_null=True)

    class Meta:
        model = Department
        fields = ('pk', 'company', 'upper_depart', 'level', 'name', 'task', 'manager', 'manager_name')
        read_only_fields = ('level',)


class PositionsInGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ('name',)


class JobGradeSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')

    class Meta:
        model = JobGrade
        fields = ('pk', 'company', 'code', 'role', 'min_promotion_years', 'promotion_criteria', 'positions')


class GradesInPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobGrade
        fields = ('code',)


class PositionSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')

    class Meta:
        model = Position
        fields = ('pk', 'company', 'name', 'grades', 'desc')


class DutyTitleSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')

    class Meta:
        model = DutyTitle
        fields = ('pk', 'company', 'name', 'desc')


# Staff ----------------------------------------------------------------------------
class StaffAssignmentSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    department_name = serializers.CharField(source='department.name', read_only=True)
    position_name = serializers.CharField(source='position.name', read_only=True)
    duty_name = serializers.CharField(source='duty.name', read_only=True)
    represent_type_desc = serializers.CharField(source='get_represent_type_display', read_only=True)

    class Meta:
        model = StaffAssignment
        fields = ('pk', 'company', 'staff', 'department', 'department_name',
                  'position', 'position_name', 'duty', 'duty_name',
                  'is_primary', 'assigned_tasks', 'represent_type', 'represent_type_desc')


class StaffSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    sort = serializers.ChoiceField(choices=Staff.SORT_CHOICES)
    sort_desc = serializers.CharField(source='get_sort_display', read_only=True)
    department = serializers.CharField(source='department.name', read_only=True, allow_null=True)
    position = serializers.CharField(source='position.name', read_only=True, allow_null=True)
    duty = serializers.CharField(source='duty.name', read_only=True, allow_null=True)
    department_name = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    position_name = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    duty_name = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    grade = serializers.SlugRelatedField(queryset=JobGrade.objects.all(), slug_field='code', allow_null=True, required=False)
    status = serializers.ChoiceField(choices=Staff.STATUS_CHOICES)
    status_desc = serializers.CharField(source='get_status_display', read_only=True)
    assignments = StaffAssignmentSerializer(many=True, read_only=True)

    class Meta:
        model = Staff
        fields = ('pk', 'company', 'sort', 'sort_desc', 'name', 'id_number', 'personal_phone',
                  'email', 'department', 'position', 'duty', 'department_name', 'position_name', 'duty_name',
                  'grade', 'date_join', 'status', 'status_desc', 'date_leave', 'user',
                  'is_hq_financial_officer', 'is_hq_hr_officer', 'assignments')

    def create(self, validated_data):
        dept_name = validated_data.pop('department_name', None) or self.initial_data.get('department')
        pos_name = validated_data.pop('position_name', None) or self.initial_data.get('position')
        duty_name = validated_data.pop('duty_name', None) or self.initial_data.get('duty')

        staff = Staff.objects.create(**validated_data)

        # 주보직 자동 생성
        self._sync_primary_assignment(staff, dept_name, pos_name, duty_name)
        return staff

    def update(self, instance, validated_data):
        dept_name = validated_data.pop('department_name', None) or self.initial_data.get('department')
        pos_name = validated_data.pop('position_name', None) or self.initial_data.get('position')
        duty_name = validated_data.pop('duty_name', None) or self.initial_data.get('duty')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 주보직 자동 동기화
        if dept_name is not None or pos_name is not None or duty_name is not None:
            self._sync_primary_assignment(instance, dept_name, pos_name, duty_name)
        return instance

    def _sync_primary_assignment(self, staff, dept_name, pos_name, duty_name):
        company = staff.company
        dept = Department.objects.filter(company=company, name=dept_name).first() if dept_name else None
        pos = Position.objects.filter(company=company, name=pos_name).first() if pos_name else None
        duty = DutyTitle.objects.filter(company=company, name=duty_name).first() if duty_name else None

        if not dept:
            # 부서명이 없으면 기존 주보직 유지 혹은 아무 작업 안 함
            return

        primary = staff.assignments.filter(is_primary=True).first()
        if primary:
            primary.department = dept
            primary.position = pos
            primary.duty = duty
            primary.save()
        else:
            StaffAssignment.objects.create(
                company=company,
                staff=staff,
                department=dept,
                position=pos,
                duty=duty,
                is_primary=True,
                assigned_tasks='기본 주보직',
            )
