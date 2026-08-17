from django.utils import timezone
from rest_framework import serializers

from approval.models import DocumentType, RouteTemplate, ApprovalDocument, ApprovalStep, ApprovalAction
from django.contrib.auth import get_user_model

User = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    class Meta:
        model = User
        fields = ('id', 'username', 'full_name')


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
    route_templates = RouteTemplateSerializer(many=True, read_only=True)

    class Meta:
        model = DocumentType
        fields = ('id', 'name', 'code', 'description', 'form_schema', 'is_active', 'route_templates')


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

    class Meta:
        model = ApprovalDocument
        fields = ('id', 'doc_number', 'title', 'doc_type', 'doc_type_name', 'drafter',
                  'status', 'current_step', 'created_at', 'submitted_at', 'completed_at')


class ApprovalDocumentSerializer(serializers.ModelSerializer):
    drafter = SimpleUserSerializer(read_only=True)
    doc_type_detail = DocumentTypeSerializer(source='doc_type', read_only=True)
    steps = ApprovalStepSerializer(many=True, read_only=True)
    pdf_url = serializers.SerializerMethodField()

    def get_pdf_url(self, obj):
        if obj.pdf_file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.pdf_file.url) if request else obj.pdf_file.url
        return None

    class Meta:
        model = ApprovalDocument
        fields = ('id', 'doc_number', 'title', 'doc_type', 'doc_type_detail',
                  'content', 'attachment', 'drafter', 'workspace',
                  'status', 'current_step', 'content_hash',
                  'pdf_url', 'created_at', 'submitted_at', 'completed_at',
                  'steps')
        read_only_fields = ('doc_number', 'drafter', 'status', 'current_step',
                            'content_hash', 'pdf_url', 'submitted_at', 'completed_at', 'steps')


class ApprovalActionCreateSerializer(serializers.Serializer):
    """결재 행동 요청 (승인/반려/의견)"""
    action = serializers.ChoiceField(choices=ApprovalAction.ACTION_CHOICES)
    comment = serializers.CharField(required=False, allow_blank=True, default='')
