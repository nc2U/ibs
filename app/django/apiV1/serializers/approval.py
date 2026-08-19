from rest_framework import serializers
from approval.models import (
    DocCategory, DocumentType, ApprovalPolicyRule,
    RouteTemplate, ApprovalDocument, ApprovalStep, ApprovalAction
)
from django.contrib.auth import get_user_model

User = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        # Profile.name 우선, 없으면 username 반환
        try:
            return obj.profile.name or obj.username
        except Exception:
            return obj.username

    class Meta:
        model = User
        fields = ('id', 'username', 'full_name')


class DocCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocCategory
        fields = ('id', 'name', 'code', 'description', 'order', 'is_active')


class ApprovalPolicyRuleSerializer(serializers.ModelSerializer):
    final_approval_duty_name = serializers.CharField(source='final_approval_duty.name', read_only=True)

    class Meta:
        model = ApprovalPolicyRule
        fields = ('id', 'name', 'min_amount', 'max_amount',
                  'final_approval_duty', 'final_approval_duty_name', 'final_dept_level', 'priority')


class RouteTemplateSerializer(serializers.ModelSerializer):
    approvers = SimpleUserSerializer(many=True, read_only=True)
    approver_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(),
        source='approvers', write_only=True
    )

    class Meta:
        model = RouteTemplate
        fields = ('id', 'step_order', 'role_label', 'approvers', 'approver_ids', 'condition')


class DocumentTypeSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    route_templates = RouteTemplateSerializer(many=True, read_only=True)
    policy_rules = ApprovalPolicyRuleSerializer(many=True, read_only=True)
    route_type_desc = serializers.CharField(source='get_route_type_display', read_only=True)
    final_approval_duty_name = serializers.CharField(source='final_approval_duty.name', read_only=True)

    class Meta:
        model = DocumentType
        fields = ('id', 'category', 'category_name', 'name', 'code', 'description',
                  'route_type', 'route_type_desc',
                  'final_approval_duty', 'final_approval_duty_name', 'final_dept_level',
                  'policy_rules', 'allowed_departments', 'allowed_duties', 'allowed_positions',
                  'form_schema', 'is_active', 'route_templates')


class ApprovalActionSerializer(serializers.ModelSerializer):
    approver = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ApprovalAction
        fields = ('id', 'approver', 'action', 'comment', 'acted_at')
        read_only_fields = ('approver', 'acted_at')


class ApprovalStepSerializer(serializers.ModelSerializer):
    approvers = SimpleUserSerializer(many=True, read_only=True)
    actions = ApprovalActionSerializer(many=True, read_only=True)

    class Meta:
        model = ApprovalStep
        fields = ('id', 'step_order', 'role_label', 'approvers', 'condition', 'status', 'actions')


class ApprovalDocumentListSerializer(serializers.ModelSerializer):
    drafter = SimpleUserSerializer(read_only=True)
    doc_type_name = serializers.CharField(source='doc_type.name', read_only=True)
    drafter_assignment_desc = serializers.SerializerMethodField()

    def get_drafter_assignment_desc(self, obj):
        if obj.drafter_assignment:
            dept = obj.drafter_assignment.department.name if obj.drafter_assignment.department else ''
            duty = obj.drafter_assignment.duty.name if obj.drafter_assignment.duty else (
                obj.drafter_assignment.position.name if obj.drafter_assignment.position else ''
            )
            return f'{dept} {duty}'.strip()
        return ''

    class Meta:
        model = ApprovalDocument
        fields = ('id', 'doc_number', 'title', 'doc_type', 'doc_type_name', 'drafter',
                  'drafter_assignment', 'drafter_assignment_desc',
                  'status', 'current_step', 'created_at', 'submitted_at', 'completed_at')


class ApprovalDocumentSerializer(serializers.ModelSerializer):
    drafter = SimpleUserSerializer(read_only=True)
    doc_type_detail = DocumentTypeSerializer(source='doc_type', read_only=True)
    steps = ApprovalStepSerializer(many=True, read_only=True)
    drafter_assignment_desc = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()

    def get_drafter_assignment_desc(self, obj):
        if obj.drafter_assignment:
            dept = obj.drafter_assignment.department.name if obj.drafter_assignment.department else ''
            duty = obj.drafter_assignment.duty.name if obj.drafter_assignment.duty else (
                obj.drafter_assignment.position.name if obj.drafter_assignment.position else ''
            )
            return f'{dept} {duty}'.strip()
        return ''

    def get_pdf_url(self, obj):
        if obj.pdf_file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.pdf_file.url) if request else obj.pdf_file.url
        return None

    class Meta:
        model = ApprovalDocument
        fields = ('id', 'doc_number', 'title', 'doc_type', 'doc_type_detail',
                  'content', 'attachment', 'drafter', 'drafter_assignment', 'drafter_assignment_desc',
                  'workspace', 'status', 'current_step', 'content_hash',
                  'pdf_url', 'created_at', 'submitted_at', 'completed_at',
                  'steps')
        read_only_fields = ('doc_number', 'drafter', 'status', 'current_step',
                            'content_hash', 'pdf_url', 'submitted_at', 'completed_at', 'steps')


class RoutePreviewStepSerializer(serializers.Serializer):
    step_order = serializers.IntegerField()
    role_label = serializers.CharField()
    approvers = SimpleUserSerializer(many=True)
    condition = serializers.CharField()


class ApprovalActionCreateSerializer(serializers.Serializer):
    """결재 행동 요청 (승인/반려/의견)"""
    action = serializers.ChoiceField(choices=ApprovalAction.ACTION_CHOICES)
    comment = serializers.CharField(required=False, allow_blank=True, default='')
