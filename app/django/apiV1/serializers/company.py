from rest_framework import serializers

from company.models import Company, Logo, Department, JobRank, Staff


# Company --------------------------------------------------------------------------
class DepartsInCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('pk', 'upper_depart', 'name', 'task')


class RanksInCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRank
        fields = ('pk', 'rank', 'title', 'description')


class CompanySerializer(serializers.ModelSerializer):
    departments = DepartsInCompanySerializer(many=True, read_only=True)
    positions = RanksInCompanySerializer(many=True, read_only=True)

    class Meta:
        model = Company
        fields = ('pk', 'name', 'ceo', 'tax_number', 'org_number', 'business_cond',
                  'business_even', 'es_date', 'op_date', 'zipcode', 'address1',
                  'address2', 'address3', 'departments', 'positions')


class LogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Logo
        fields = ('pk', 'company', 'generic_logo', 'dark_logo', 'simple_logo')


class StaffsInDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ('pk', 'position', 'name')


class DepartmentSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    staffs = StaffsInDepartmentSerializer(many=True, read_only=True)

    class Meta:
        model = Department
        fields = ('pk', 'company', 'upper_depart', 'level', 'name', 'task', 'staffs')


class JobRankSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    sort = serializers.ChoiceField(choices=JobRank.SORT_CHOICES)
    sort_desc = serializers.CharField(source='get_sort_display', read_only=True)

    class Meta:
        model = JobRank
        fields = ('pk', 'company', 'sort', 'sort_desc', 'rank', 'title', 'description')


class StaffSerializer(serializers.ModelSerializer):
    department = serializers.SlugRelatedField(queryset=Department.objects.all(), slug_field='name')
    rank = serializers.SlugRelatedField(queryset=JobRank.objects.all(), slug_field='rank')
    gender = serializers.ChoiceField(choices=Staff.GENDER_CHOICES)
    gender_desc = serializers.CharField(source='get_gender_display', read_only=True)
    status = serializers.ChoiceField(choices=Staff.STATUS_CHOICES)
    status_desc = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Staff
        fields = ('pk', 'department', 'rank', 'name', 'birth_date', 'gender', 'gender_desc',
                  'entered_date', 'personal_phone', 'email', 'status', 'status_desc')
