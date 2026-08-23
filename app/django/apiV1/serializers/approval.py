from rest_framework import serializers
from approval.models import (
    DocCategory, DocumentType, ApprovalPolicyRule,
    RouteTemplate, ApprovalDocument, ApprovalStep, ApprovalAction, ApprovalDelegation, ApprovalAttachment
)
from django.contrib.auth import get_user_model
import json

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


class ApprovalDelegationSerializer(serializers.ModelSerializer):
    """결재 권한 위임 (대결) Serializer"""
    delegator = SimpleUserSerializer(read_only=True)
    delegator_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='delegator', write_only=True, required=False
    )
    delegatee = SimpleUserSerializer(read_only=True)
    delegatee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='delegatee', write_only=True
    )
    is_valid_now = serializers.BooleanField(source='is_currently_valid', read_only=True)

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({'end_date': '위임 종료일은 시작일 이후여야 합니다.'})
        return attrs

    class Meta:
        model = ApprovalDelegation
        fields = (
            'id', 'delegator', 'delegator_id', 'delegatee', 'delegatee_id',
            'start_date', 'end_date', 'reason', 'is_active', 'is_valid_now',
            'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')


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
    default_security_level_desc = serializers.CharField(source='get_default_security_level_display', read_only=True)
    final_approval_duty_name = serializers.CharField(source='final_approval_duty.name', read_only=True)

    class Meta:
        model = DocumentType
        fields = ('id', 'category', 'category_name', 'name', 'code', 'description',
                  'form_template_key', 'default_security_level', 'default_security_level_desc',
                  'route_type', 'route_type_desc',
                  'final_approval_duty', 'final_approval_duty_name', 'final_dept_level',
                  'policy_rules', 'allowed_departments', 'allowed_duties', 'allowed_positions',
                  'is_active', 'route_templates')


class ApprovalActionSerializer(serializers.ModelSerializer):
    approver = SimpleUserSerializer(read_only=True)
    delegated_from = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ApprovalAction
        fields = ('id', 'approver', 'is_delegated', 'delegated_from', 'action', 'comment', 'acted_at')
        read_only_fields = ('approver', 'is_delegated', 'delegated_from', 'acted_at')


class ApprovalAttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    creator_name = serializers.CharField(source='creator.profile.name', read_only=True, default='')

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None

    class Meta:
        model = ApprovalAttachment
        fields = ('id', 'document', 'file', 'file_url', 'file_name', 'file_type', 'file_size',
                  'creator', 'creator_name', 'created_at')
        read_only_fields = ('file_name', 'file_type', 'file_size', 'creator', 'created_at')


class ApprovalStepSerializer(serializers.ModelSerializer):
    approvers = SimpleUserSerializer(many=True, read_only=True)
    actions = ApprovalActionSerializer(many=True, read_only=True)

    class Meta:
        model = ApprovalStep
        fields = ('id', 'step_order', 'role_label', 'approvers', 'condition', 'status', 'actions')


class ApprovalDocumentListSerializer(serializers.ModelSerializer):
    drafter = SimpleUserSerializer(read_only=True)
    drafter_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='doc_type.category.name', read_only=True, allow_null=True)
    doc_type_name = serializers.CharField(source='doc_type.name', read_only=True)
    department_name = serializers.CharField(source='drafter_assignment.department.name', read_only=True, allow_null=True)
    drafter_assignment_desc = serializers.SerializerMethodField()
    status_desc = serializers.CharField(source='get_status_display', read_only=True)
    security_level_desc = serializers.CharField(source='get_security_level_display', read_only=True)
    attachment_count = serializers.IntegerField(source='attachments.count', read_only=True)
    observer_count = serializers.IntegerField(source='observers.count', read_only=True)

    def get_drafter_name(self, obj):
        if obj.drafter:
            profile = getattr(obj.drafter, 'profile', None)
            if profile and profile.name:
                return profile.name
            return obj.drafter.username
        return ''

    def get_drafter_assignment_desc(self, obj):
        if obj.drafter_assignment:
            dept = obj.drafter_assignment.department.name if obj.drafter_assignment.department else ''
            duty = obj.drafter_assignment.duty.name if obj.drafter_assignment.duty else (
                obj.drafter_assignment.staff.position.name if obj.drafter_assignment.staff and obj.drafter_assignment.staff.position else ''
            )
            return f'{dept} {duty}'.strip()
        return ''

    class Meta:
        model = ApprovalDocument
        fields = ('id', 'doc_number', 'title', 'doc_type', 'doc_type_name', 'category_name', 'drafter',
                  'drafter_name', 'drafter_assignment', 'department_name', 'drafter_assignment_desc',
                  'attachment_count', 'observer_count', 'security_level', 'security_level_desc',
                  'status', 'status_desc', 'current_step',
                  'created_at', 'submitted_at', 'completed_at')


class ApprovalDocumentSerializer(serializers.ModelSerializer):
    drafter = SimpleUserSerializer(read_only=True)
    drafter_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='doc_type.category.name', read_only=True, allow_null=True)
    doc_type_name = serializers.CharField(source='doc_type.name', read_only=True)
    department_name = serializers.CharField(source='drafter_assignment.department.name', read_only=True, allow_null=True)
    status_desc = serializers.CharField(source='get_status_display', read_only=True)
    security_level_desc = serializers.CharField(source='get_security_level_display', read_only=True)
    doc_type_detail = DocumentTypeSerializer(source='doc_type', read_only=True)
    steps = ApprovalStepSerializer(many=True, read_only=True)
    attachments = ApprovalAttachmentSerializer(many=True, read_only=True)
    observers = SimpleUserSerializer(many=True, read_only=True)
    observer_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), source='observers', required=False, write_only=True
    )
    drafter_assignment_desc = serializers.SerializerMethodField()
    content = serializers.DictField(required=False, default=dict)
    pdf_url = serializers.SerializerMethodField()

    def get_drafter_name(self, obj):
        if obj.drafter:
            profile = getattr(obj.drafter, 'profile', None)
            if profile and profile.name:
                return profile.name
            return obj.drafter.username
        return ''

    def get_drafter_assignment_desc(self, obj):
        if obj.drafter_assignment:
            dept = obj.drafter_assignment.department.name if obj.drafter_assignment.department else ''
            duty = obj.drafter_assignment.duty.name if obj.drafter_assignment.duty else (
                obj.drafter_assignment.staff.position.name if obj.drafter_assignment.staff and obj.drafter_assignment.staff.position else ''
            )
            return f'{dept} {duty}'.strip()
        return ''

    def get_pdf_url(self, obj):
        if hasattr(obj, 'pdf_file') and obj.pdf_file and obj.pdf_file.name:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.pdf_file.url) if request else obj.pdf_file.url
        # 최종 승인된 문서인데 PDF가 아직 없거나 누락된 경우 즉시 온디맨드로 생성 및 S3 저장
        if getattr(obj, 'status', None) == ApprovalDocument.STATUS_APPROVED:
            try:
                from approval.tasks import render_and_save_approval_pdf
                render_and_save_approval_pdf(obj.pk)
                obj.refresh_from_db()
                if obj.pdf_file and obj.pdf_file.name:
                    request = self.context.get('request')
                    return request.build_absolute_uri(obj.pdf_file.url) if request else obj.pdf_file.url
            except Exception as e:
                print(f'⚠️ On-demand PDF generation failed for doc {obj.pk}: {e}')
        return None

    def to_internal_value(self, data):
        mutable_data = data.copy() if hasattr(data, 'copy') else dict(data)
        content_val = mutable_data.get('content')
        if content_val is not None:
            if isinstance(content_val, (list, tuple)):
                content_val = content_val[0] if content_val else '{}'
            if isinstance(content_val, str):
                content_val = content_val.strip()
                if not content_val:
                    mutable_data['content'] = {}
                else:
                    try:
                        mutable_data['content'] = json.loads(content_val)
                    except Exception:
                        mutable_data['content'] = {}
        else:
            mutable_data['content'] = {}

        # observer_ids가 문자열/JSON 또는 multipart-formdata로 넘어온 경우 처리
        observer_val = mutable_data.get('observer_ids')
        if isinstance(observer_val, str):
            try:
                parsed = json.loads(observer_val)
                if isinstance(parsed, list):
                    mutable_data.setlist('observer_ids', parsed) if hasattr(mutable_data, 'setlist') else mutable_data.update({'observer_ids': parsed})
            except Exception:
                pass

        return super().to_internal_value(mutable_data)

    def create(self, validated_data):
        request = self.context.get('request')
        observers_data = validated_data.pop('observers', None)
        document = super().create(validated_data)

        if observers_data is not None:
            document.observers.set(observers_data)

        # 다중 첨부파일 업로드 처리
        if request and request.FILES:
            files = request.FILES.getlist('files') or request.FILES.getlist('attachments')
            for f in files:
                ApprovalAttachment.objects.create(
                    document=document,
                    file=f,
                    creator=request.user if request.user.is_authenticated else None,
                )
        return document

    def update(self, instance, validated_data):
        request = self.context.get('request')
        observers_data = validated_data.pop('observers', None)
        document = super().update(instance, validated_data)

        if observers_data is not None:
            document.observers.set(observers_data)

        # 다중 첨부파일 추가 업로드 처리
        if request and request.FILES:
            files = request.FILES.getlist('files') or request.FILES.getlist('attachments')
            for f in files:
                ApprovalAttachment.objects.create(
                    document=document,
                    file=f,
                    creator=request.user if request.user.is_authenticated else None,
                )
        return document

    class Meta:
        model = ApprovalDocument
        fields = ('id', 'doc_number', 'title', 'doc_type', 'doc_type_name', 'category_name',
                  'doc_type_detail', 'content', 'attachment', 'attachments', 'observers', 'observer_ids',
                  'drafter', 'drafter_name', 'drafter_assignment', 'department_name', 'drafter_assignment_desc',
                  'workspace', 'security_level', 'security_level_desc',
                  'status', 'status_desc', 'current_step', 'content_hash',
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
