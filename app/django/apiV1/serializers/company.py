from rest_framework import serializers

from company.models import Company, Logo, Department, JobGrade, Position, DutyTitle, Staff
from work.models import IssueProject


# Company --------------------------------------------------------------------------
class DepartsInCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('pk', 'upper_depart', 'name', 'task')


class GradesInCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobGrade
        fields = ('pk', 'name', 'promotion_period', 'criteria_new')


class CompanySerializer(serializers.ModelSerializer):
    departments = DepartsInCompanySerializer(many=True, read_only=True)
    grades = GradesInCompanySerializer(many=True, read_only=True)
    com_issue_project = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Company
        fields = ('pk', 'name', 'ceo', 'tax_number', 'org_number', 'business_cond',
                  'business_even', 'es_date', 'op_date', 'zipcode', 'address1',
                  'address2', 'address3', 'departments', 'grades', 'com_issue_project')

    @staticmethod
    def get_com_issue_project(obj):
        issue_project = IssueProject.objects.filter(company=obj, sort='1').first()
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
    staffs = StaffsInDepartmentSerializer(many=True, read_only=True)

    class Meta:
        model = Department
        fields = ('pk', 'company', 'upper_depart', 'level', 'name', 'task', 'staffs')


class PositionsInGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ('name',)


class JobGradeSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')

    class Meta:
        model = JobGrade
        fields = ('pk', 'company', 'name', 'promotion_period', 'criteria_new', 'positions')


class GradesInPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobGrade
        fields = ('name',)


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


class StaffSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    sort = serializers.ChoiceField(choices=Staff.SORT_CHOICES)
    sort_desc = serializers.CharField(source='get_sort_display', read_only=True)
    department = serializers.SlugRelatedField(queryset=Department.objects.all(), slug_field='name', allow_null=True)
    grade = serializers.SlugRelatedField(queryset=JobGrade.objects.all(), slug_field='name', allow_null=True)
    position = serializers.SlugRelatedField(queryset=Position.objects.all(), slug_field='name', allow_null=True)
    duty = serializers.SlugRelatedField(queryset=DutyTitle.objects.all(), slug_field='name', allow_null=True)
    status = serializers.ChoiceField(choices=Staff.STATUS_CHOICES)
    status_desc = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Staff
        fields = ('pk', 'company', 'sort', 'sort_desc', 'name', 'id_number',
                  'personal_phone', 'email', 'department', 'grade', 'position',
                  'duty', 'date_join', 'status', 'status_desc', 'date_leave', 'user')
