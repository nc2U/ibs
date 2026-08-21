from django.contrib import admin
from approval.models import (
    DocCategory, DocumentType, ApprovalPolicyRule,
    RouteTemplate, ApprovalDocument, ApprovalStep, ApprovalAction, ApprovalAttachment
)


@admin.register(DocCategory)
class DocCategoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'code', 'name', 'description', 'is_active')
    list_display_links = ('code', 'name')
    list_editable = ('order', 'is_active')
    search_fields = ('code', 'name')


class ApprovalPolicyRuleInline(admin.TabularInline):
    model = ApprovalPolicyRule
    extra = 1


class RouteTemplateInline(admin.TabularInline):
    model = RouteTemplate
    extra = 1
    filter_horizontal = ('approvers',)


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('category', 'code', 'name', 'form_template_key', 'route_type', 'final_approval_duty',
                    'final_dept_level', 'is_active', 'created_at')
    list_filter = ('category', 'form_template_key', 'route_type', 'is_active')
    list_display_links = ('code', 'name')
    search_fields = ('code', 'name')
    filter_horizontal = ('allowed_departments', 'allowed_duties', 'allowed_positions')
    inlines = [ApprovalPolicyRuleInline, RouteTemplateInline]


@admin.register(ApprovalPolicyRule)
class ApprovalPolicyRuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'doc_type', 'name', 'min_amount', 'max_amount', 'final_approval_duty',
                    'final_dept_level', 'priority')
    list_display_links = ('name',)
    list_filter = ('doc_type', 'final_approval_duty', 'final_dept_level')
    search_fields = ('name', 'doc_type__name')
    ordering = ('doc_type', 'priority', 'id')


@admin.register(RouteTemplate)
class RouteTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'doc_type', 'step_order', 'role_label', 'condition')
    list_display_links = ('role_label',)
    list_filter = ('doc_type', 'condition')
    search_fields = ('role_label', 'doc_type__name')
    filter_horizontal = ('approvers',)
    ordering = ('doc_type', 'step_order')


class ApprovalStepInline(admin.TabularInline):
    model = ApprovalStep
    extra = 0
    readonly_fields = ('step_order', 'role_label', 'condition', 'status')
    filter_horizontal = ('approvers',)


class ApprovalActionInline(admin.TabularInline):
    model = ApprovalAction
    extra = 0
    readonly_fields = ('approver', 'action', 'comment', 'content_hash', 'acted_at')
    can_delete = False


class ApprovalAttachmentInline(admin.TabularInline):
    model = ApprovalAttachment
    extra = 0
    readonly_fields = ('file_name', 'file_type', 'file_size', 'created_at', 'creator')


@admin.register(ApprovalDocument)
class ApprovalDocumentAdmin(admin.ModelAdmin):
    list_display = ('doc_number', 'title', 'doc_type', 'drafter', 'drafter_assignment', 'status', 'created_at',
                    'submitted_at', 'completed_at')
    list_filter = ('status', 'doc_type', 'created_at')
    search_fields = ('title', 'drafter__username', 'doc_number')
    readonly_fields = ('doc_number', 'content_hash', 'created_at', 'updated_at', 'submitted_at', 'completed_at')
    filter_horizontal = ('observers',)
    inlines = [ApprovalAttachmentInline, ApprovalStepInline]


@admin.register(ApprovalStep)
class ApprovalStepAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'step_order', 'role_label', 'condition', 'status')
    list_filter = ('status', 'condition')
    search_fields = ('role_label', 'document__title', 'document__doc_number')
    filter_horizontal = ('approvers',)
    inlines = [ApprovalActionInline]


@admin.register(ApprovalAction)
class ApprovalActionAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_document', 'step', 'approver', 'action', 'comment', 'acted_at')
    list_filter = ('action', 'acted_at')
    search_fields = ('approver__username', 'comment', 'content_hash', 'step__document__title',
                     'step__document__doc_number')
    readonly_fields = ('step', 'approver', 'action', 'comment', 'content_hash', 'acted_at')

    @admin.display(description='결재 문서')
    def get_document(self, obj):
        return obj.step.document.title if obj.step and obj.step.document else '-'


@admin.register(ApprovalAttachment)
class ApprovalAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'file_name', 'file_type', 'file_size', 'creator', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('file_name', 'document__title', 'document__doc_number')
