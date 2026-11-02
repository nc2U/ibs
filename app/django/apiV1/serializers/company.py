from rest_framework import serializers

from company.models import (
    Company, Logo, CompanySeal, Department, JobGrade, Position, DutyTitle,
    ExecutiveRank, Executive, Staff, StaffAssignment,
    PersonnelOrder, StaffCareer, StaffCertificate, StaffRewardPunishment,
    StaffLeaveQuota, StaffLeaveUsage,
    PromotionPolicy, StaffEvaluation, PromotionCandidate
)
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

    representative_name = serializers.CharField(source='get_representative_staff_name', read_only=True)

    class Meta:
        model = Company
        fields = ('pk', 'name', 'en_name', 'short_name', 'ceo', 'representative_name', 'tax_number', 'org_number',
                  'business_cond', 'business_even', 'es_date', 'op_date', 'zipcode', 'address1',
                  'address2', 'address3', 'phone', 'fax', 'email', 'departments', 'grades', 'com_issue_project', 'is_default')

    @staticmethod
    def get_com_issue_project(obj):
        issue_project = IssueProject.objects.filter(company=obj, type='1').first()
        return issue_project.pk if issue_project else None


class LogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Logo
        fields = ('pk', 'company', 'generic_logo', 'dark_logo', 'simple_logo')


class CompanySealSerializer(serializers.ModelSerializer):
    seal_type_desc = serializers.CharField(source='get_seal_type_display', read_only=True)
    custody_type_desc = serializers.CharField(source='get_custody_type_display', read_only=True)
    internal_manager_name = serializers.CharField(source='internal_manager.name', read_only=True, allow_null=True)
    internal_manager_duty = serializers.SerializerMethodField(read_only=True)
    final_approval_duty_name = serializers.CharField(source='final_approval_duty.name', read_only=True, allow_null=True)
    route_template_name = serializers.CharField(source='route_template.role_label', read_only=True, allow_null=True)

    class Meta:
        model = CompanySeal
        fields = ('pk', 'company', 'seal_type', 'seal_type_desc', 'name', 'purpose', 'seal_image',
                  'custody_type', 'custody_type_desc', 'custodian',
                  'internal_manager', 'internal_manager_name', 'internal_manager_duty',
                  'valid_from', 'valid_until', 'final_approval_duty', 'final_approval_duty_name',
                  'final_dept_level', 'route_template', 'route_template_name',
                  'is_active', 'description', 'created', 'manager')

    def get_internal_manager_duty(self, obj):
        if obj.internal_manager:
            duty = getattr(obj.internal_manager, 'duty', None)
            if duty:
                return duty.name
            pos = getattr(obj.internal_manager, 'position', None)
            if pos:
                return pos.name
        return ''


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

    def validate(self, attrs):
        company = attrs.get('company') or getattr(self.instance, 'company', None)
        upper = attrs.get('upper_depart', getattr(self.instance, 'upper_depart', None) if self.instance else None)
        manager = attrs.get('manager', getattr(self.instance, 'manager', None) if self.instance else None)

        if upper:
            if company and upper.company_id != company.pk:
                raise serializers.ValidationError({'upper_depart': '상위 부서의 소속 회사가 일치하지 않습니다.'})
            if self.instance and upper.pk == self.instance.pk:
                raise serializers.ValidationError({'upper_depart': '자기 자신을 상위 부서로 지정할 수 없습니다.'})
            parent = upper
            visited = {self.instance.pk} if self.instance else set()
            while parent:
                if parent.pk in visited:
                    raise serializers.ValidationError({'upper_depart': '상위 부서 지정 시 순환 참조가 발생합니다.'})
                visited.add(parent.pk)
                parent = parent.upper_depart

        if manager and company and manager.company_id != company.pk:
            raise serializers.ValidationError({'manager': '부서 책임자의 소속 회사가 일치하지 않습니다.'})

        return attrs


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
        fields = ('pk', 'company', 'code', 'name', 'desc')


class ExecutiveRankSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')

    class Meta:
        model = ExecutiveRank
        fields = ('pk', 'company', 'code', 'name', 'sort_order', 'role_desc')


class ExecutiveSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    full_name = serializers.ReadOnlyField()  # 응답용
    rank_name = serializers.CharField(source='rank.name', read_only=True, allow_null=True)
    executive_type_desc = serializers.CharField(source='get_executive_type_display', read_only=True)
    represent_type_desc = serializers.CharField(source='get_represent_type_display', read_only=True)

    class Meta:
        model = Executive
        fields = ('pk', 'company', 'staff', 'staff_name', 'name', 'full_name', 'contact', 'rank', 'rank_name',
                  'executive_type', 'executive_type_desc', 'is_registered', 'is_standing', 'represent_type',
                  'represent_type_desc', 'term_start', 'term_end', 'appointed_date', 'note')

    def validate(self, attrs):
        staff = attrs.get('staff', getattr(self.instance, 'staff', None) if self.instance else None)
        name = attrs.get('name', getattr(self.instance, 'name', '') if self.instance else '')
        company = attrs.get('company') or getattr(self.instance, 'company', None)
        rank = attrs.get('rank', getattr(self.instance, 'rank', None) if self.instance else None)

        if not staff and (not name or not name.strip()):
            raise serializers.ValidationError({
                'non_field_errors': ["시스템 계정(Staff) 또는 이름 중 하나는 반드시 입력해야 합니다."]
            })

        if company:
            if staff and staff.company_id != company.pk:
                raise serializers.ValidationError({'staff': '선택한 임원 직원의 회사와 임원 정보의 회사가 일치하지 않습니다.'})
            if rank and rank.company_id != company.pk:
                raise serializers.ValidationError({'rank': '선택한 임원 직위의 회사와 임원 정보의 회사가 일치하지 않습니다.'})
        return attrs


# Staff & Details ------------------------------------------------------------------
class StaffAssignmentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    department_name = serializers.CharField(source='department.name', read_only=True)
    duty_name = serializers.CharField(source='duty.name', read_only=True, allow_null=True)
    position_name = serializers.CharField(source='staff.position.name', read_only=True, allow_null=True)

    class Meta:
        model = StaffAssignment
        fields = ('id', 'pk', 'company', 'company_name', 'staff', 'department', 'department_name',
                  'duty', 'duty_name', 'position_name', 'is_primary', 'assigned_tasks')

    def validate(self, attrs):
        company = attrs.get('company') or getattr(self.instance, 'company', None)
        staff = attrs.get('staff', getattr(self.instance, 'staff', None) if self.instance else None)
        department = attrs.get('department', getattr(self.instance, 'department', None) if self.instance else None)
        duty = attrs.get('duty', getattr(self.instance, 'duty', None) if self.instance else None)

        if company:
            if staff and staff.company_id != company.pk:
                raise serializers.ValidationError({'staff': '직원의 소속 회사와 보직 정보의 소속 회사가 일치하지 않습니다.'})
            if department and department.company_id != company.pk:
                raise serializers.ValidationError({'department': '소속 부서의 회사와 보직 정보의 소속 회사가 일치하지 않습니다.'})
            if duty and duty.company_id != company.pk:
                raise serializers.ValidationError({'duty': '직책의 소속 회사와 보직 정보의 소속 회사가 일치하지 않습니다.'})
        return attrs


class PersonnelOrderSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    order_type_desc = serializers.CharField(source='get_order_type_display', read_only=True)
    prev_department_name = serializers.CharField(source='prev_department.name', read_only=True, allow_null=True)
    prev_grade_code = serializers.CharField(source='prev_grade.code', read_only=True, allow_null=True)
    prev_position_name = serializers.CharField(source='prev_position.name', read_only=True, allow_null=True)
    prev_duty_name = serializers.CharField(source='prev_duty.name', read_only=True, allow_null=True)
    new_department_name = serializers.CharField(source='new_department.name', read_only=True, allow_null=True)
    new_grade_code = serializers.CharField(source='new_grade.code', read_only=True, allow_null=True)
    new_position_name = serializers.CharField(source='new_position.name', read_only=True, allow_null=True)
    new_duty_name = serializers.CharField(source='new_duty.name', read_only=True, allow_null=True)

    class Meta:
        model = PersonnelOrder
        fields = ('id', 'pk', 'company', 'company_name', 'staff', 'staff_name', 'order_type', 'order_type_desc',
                  'order_date', 'effective_end_date', 'order_no',
                  'prev_department', 'prev_department_name', 'prev_grade', 'prev_grade_code',
                  'prev_position', 'prev_position_name', 'prev_duty', 'prev_duty_name',
                  'new_department', 'new_department_name', 'new_grade', 'new_grade_code',
                  'new_position', 'new_position_name', 'new_duty', 'new_duty_name',
                  'description', 'is_processed')

    def validate(self, attrs):
        company = attrs.get('company') or getattr(self.instance, 'company', None)
        staff = attrs.get('staff', getattr(self.instance, 'staff', None) if self.instance else None)
        new_dept = attrs.get('new_department', getattr(self.instance, 'new_department', None) if self.instance else None)
        new_grade = attrs.get('new_grade', getattr(self.instance, 'new_grade', None) if self.instance else None)
        new_pos = attrs.get('new_position', getattr(self.instance, 'new_position', None) if self.instance else None)
        new_duty = attrs.get('new_duty', getattr(self.instance, 'new_duty', None) if self.instance else None)

        if company:
            if staff and staff.company_id != company.pk:
                raise serializers.ValidationError({'staff': '발령 대상 직원의 소속 회사와 발령 정보의 소속 회사가 일치하지 않습니다.'})
            if new_dept and new_dept.company_id != company.pk:
                raise serializers.ValidationError({'new_department': '발령 부서의 소속 회사가 일치하지 않습니다.'})
            if new_grade and new_grade.company_id != company.pk:
                raise serializers.ValidationError({'new_grade': '발령 직급의 소속 회사가 일치하지 않습니다.'})
            if new_pos and new_pos.company_id != company.pk:
                raise serializers.ValidationError({'new_position': '발령 직위의 소속 회사가 일치하지 않습니다.'})
            if new_duty and new_duty.company_id != company.pk:
                raise serializers.ValidationError({'new_duty': '발령 직책의 소속 회사가 일치하지 않습니다.'})
        return attrs


class StaffCareerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk', read_only=True)
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    staff_name = serializers.CharField(source='staff.name', read_only=True)

    class Meta:
        model = StaffCareer
        fields = ('id', 'pk', 'company', 'staff', 'staff_name', 'company_name', 'department_name',
                  'position_title', 'assigned_tasks', 'start_date', 'end_date', 'recognized_ratio', 'note')


class StaffCertificateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk', read_only=True)
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    staff_name = serializers.CharField(source='staff.name', read_only=True)

    class Meta:
        model = StaffCertificate
        fields = ('id', 'pk', 'company', 'staff', 'staff_name', 'name', 'grade',
                  'cert_number', 'issuer', 'acquired_date', 'expire_date', 'has_allowance', 'note')


class StaffRewardPunishmentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk', read_only=True)
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    sort_desc = serializers.CharField(source='get_sort_display', read_only=True)

    class Meta:
        model = StaffRewardPunishment
        fields = ('id', 'pk', 'company', 'staff', 'staff_name', 'sort', 'sort_desc',
                  'type_name', 'action_date', 'expire_date', 'reason', 'organization', 'note')


class StaffLeaveQuotaSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk', read_only=True)
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    total_granted_days = serializers.DecimalField(max_digits=4, decimal_places=2, read_only=True)
    used_days = serializers.DecimalField(max_digits=4, decimal_places=2, read_only=True)
    remaining_days = serializers.DecimalField(max_digits=4, decimal_places=2, read_only=True)

    class Meta:
        model = StaffLeaveQuota
        fields = ('id', 'pk', 'company', 'staff', 'staff_name', 'year',
                  'granted_days', 'carry_over_days', 'reward_days',
                  'total_granted_days', 'used_days', 'remaining_days',
                  'valid_start', 'valid_end', 'note')

    def validate(self, attrs):
        company = attrs.get('company') or getattr(self.instance, 'company', None)
        staff = attrs.get('staff', getattr(self.instance, 'staff', None) if self.instance else None)
        if company and staff and staff.company_id != company.pk:
            raise serializers.ValidationError({'staff': '직원의 소속 회사와 연차 관리의 소속 회사가 일치하지 않습니다.'})
        return attrs


class StaffLeaveUsageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk', read_only=True)
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    leave_type_desc = serializers.CharField(source='get_leave_type_display', read_only=True)

    class Meta:
        model = StaffLeaveUsage
        fields = ('id', 'pk', 'company', 'staff', 'staff_name', 'leave_type', 'leave_type_desc',
                  'start_date', 'end_date', 'deduction_days', 'approval_doc', 'reason',
                  'is_cancelled', 'created')

    def validate(self, attrs):
        company = attrs.get('company') or getattr(self.instance, 'company', None)
        staff = attrs.get('staff', getattr(self.instance, 'staff', None) if self.instance else None)
        if company and staff and staff.company_id != company.pk:
            raise serializers.ValidationError({'staff': '직원의 소속 회사와 휴가 사용의 소속 회사가 일치하지 않습니다.'})
        return attrs


class StaffSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    sort = serializers.ChoiceField(choices=Staff.SORT_CHOICES)
    sort_desc = serializers.CharField(source='get_sort_display', read_only=True)
    employment_type_desc = serializers.CharField(source='get_employment_type_display', read_only=True)
    department = serializers.CharField(source='department.name', read_only=True, allow_null=True)
    position = serializers.SlugRelatedField(queryset=Position.objects.all(), slug_field='name', allow_null=True,
                                            required=False)
    duty = serializers.CharField(source='duty.name', read_only=True, allow_null=True)
    department_name = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    position_name = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    duty_name = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    grade = serializers.SlugRelatedField(queryset=JobGrade.objects.all(), slug_field='code', allow_null=True,
                                         required=False)
    status = serializers.ChoiceField(choices=Staff.STATUS_CHOICES)
    status_desc = serializers.CharField(source='get_status_display', read_only=True)
    assignments = StaffAssignmentSerializer(many=True, read_only=True)
    executive = ExecutiveSerializer(read_only=True)

    class Meta:
        model = Staff
        fields = ('pk', 'company', 'sort', 'sort_desc', 'employment_type', 'employment_type_desc',
                  'contract_end_date', 'probation_end_date', 'name', 'id_number', 'direct_phone', 'direct_fax',
                  'personal_phone', 'email', 'department', 'position', 'duty', 'department_name', 'position_name',
                  'duty_name', 'grade', 'date_join', 'status', 'status_desc', 'date_leave', 'user',
                  'assignments', 'executive')

    def to_representation(self, instance):
        """[H-2] 본인 또는 관리자(슈퍼유저)가 아닌 경우 주민등록번호 마스킹 처리"""
        data = super().to_representation(instance)
        request = self.context.get('request')
        user = request.user if request else None

        is_owner = user and instance.user_id == user.pk
        is_admin = user and (user.is_superuser or getattr(user, 'work_manager', False))

        if not (is_owner or is_admin):
            id_num = data.get('id_number')
            if id_num:
                cleaned = str(id_num).replace('-', '').strip()
                if len(cleaned) >= 7:
                    data['id_number'] = f"{cleaned[:6]}-{'*' * (len(cleaned) - 6)}"
                else:
                    data['id_number'] = '*******'
        return data

    def create(self, validated_data):
        dept_name = validated_data.pop('department_name', None) or self.initial_data.get('department')
        pos_name = validated_data.pop('position_name', None) or self.initial_data.get('position')
        duty_name = validated_data.pop('duty_name', None) or self.initial_data.get('duty')

        if not validated_data.get('position') and pos_name:
            company = validated_data.get('company')
            validated_data['position'] = Position.objects.filter(company=company, name=pos_name).first()

        staff = Staff.objects.create(**validated_data)

        # 주보직 자동 생성
        self._sync_primary_assignment(staff, dept_name, duty_name)
        return staff

    def update(self, instance, validated_data):
        dept_name = validated_data.pop('department_name', None) or self.initial_data.get('department')
        pos_name = validated_data.pop('position_name', None) or self.initial_data.get('position')
        duty_name = validated_data.pop('duty_name', None) or self.initial_data.get('duty')

        if 'position' not in validated_data and pos_name is not None:
            company = validated_data.get('company') or instance.company
            validated_data['position'] = Position.objects.filter(company=company, name=pos_name).first()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 주보직 자동 동기화
        if dept_name is not None or duty_name is not None:
            self._sync_primary_assignment(instance, dept_name, duty_name)
        return instance

    def _sync_primary_assignment(self, staff, dept_name, duty_name):
        company = staff.company
        dept = Department.objects.filter(company=company, name=dept_name).first() if dept_name else None
        duty = DutyTitle.objects.filter(company=company, name=duty_name).first() if duty_name else None

        if not dept:
            # 부서명이 없으면 기존 주보직 유지 혹은 아무 작업 안 함
            return

        primary = staff.assignments.filter(is_primary=True).first()
        if primary:
            primary.department = dept
            primary.duty = duty
            primary.save()
        else:
            StaffAssignment.objects.create(
                company=company,
                staff=staff,
                department=dept,
                duty=duty,
                is_primary=True,
                assigned_tasks='기본 주보직',
            )


# Promotion & Evaluation -----------------------------------------------------------
class PromotionPolicySerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    current_grade_code = serializers.CharField(source='current_grade.code', read_only=True)
    target_grade_code = serializers.CharField(source='target_grade.code', read_only=True)

    class Meta:
        model = PromotionPolicy
        fields = ('pk', 'company', 'current_grade', 'current_grade_code', 'target_grade', 'target_grade_code',
                  'min_years', 'min_avg_grade_point', 'required_eval_grade', 'required_credentials',
                  'disqualification_conditions', 'description', 'is_active')


class StaffEvaluationSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    eval_period_desc = serializers.CharField(source='get_eval_period_display', read_only=True)
    evaluator_name = serializers.CharField(source='evaluator.name', read_only=True, allow_null=True)
    reviewer_name = serializers.CharField(source='reviewer.name', read_only=True, allow_null=True)

    class Meta:
        model = StaffEvaluation
        fields = ('pk', 'company', 'staff', 'staff_name', 'eval_year', 'eval_period', 'eval_period_desc',
                  'grade', 'score', 'achievement_summary', 'evaluator', 'evaluator_name',
                  'reviewer', 'reviewer_name', 'notes')

    def validate(self, attrs):
        company = attrs.get('company') or getattr(self.instance, 'company', None)
        staff = attrs.get('staff', getattr(self.instance, 'staff', None) if self.instance else None)
        evaluator = attrs.get('evaluator', getattr(self.instance, 'evaluator', None) if self.instance else None)
        reviewer = attrs.get('reviewer', getattr(self.instance, 'reviewer', None) if self.instance else None)

        if company:
            if staff and staff.company_id != company.pk:
                raise serializers.ValidationError({'staff': '피평가자의 소속 회사가 일치하지 않습니다.'})
            if evaluator and evaluator.company_id != company.pk:
                raise serializers.ValidationError({'evaluator': '1차 평가자의 소속 회사가 일치하지 않습니다.'})
            if reviewer and reviewer.company_id != company.pk:
                raise serializers.ValidationError({'reviewer': '2차 평가자의 소속 회사가 일치하지 않습니다.'})
        return attrs


class PromotionCandidateSerializer(serializers.ModelSerializer):
    company = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name')
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    current_grade_code = serializers.CharField(source='policy.current_grade.code', read_only=True)
    target_grade_code = serializers.CharField(source='policy.target_grade.code', read_only=True)
    status_desc = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PromotionCandidate
        fields = ('pk', 'company', 'policy', 'staff', 'staff_name', 'current_grade_code', 'target_grade_code',
                  'eval_year', 'tenure_years', 'avg_eval_score', 'status', 'status_desc',
                  'committee_review', 'promoted_date')

    def validate(self, attrs):
        company = attrs.get('company') or getattr(self.instance, 'company', None)
        staff = attrs.get('staff', getattr(self.instance, 'staff', None) if self.instance else None)
        policy = attrs.get('policy', getattr(self.instance, 'policy', None) if self.instance else None)

        if company:
            if staff and staff.company_id != company.pk:
                raise serializers.ValidationError({'staff': '승급 대상자의 소속 회사가 일치하지 않습니다.'})
            if policy and policy.company_id != company.pk:
                raise serializers.ValidationError({'policy': '승급 정책의 소속 회사가 일치하지 않습니다.'})
        return attrs
