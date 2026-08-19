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
    list_display = ('category', 'code', 'name', 'form_type', 'form_template_key', 'route_type', 'final_approval_duty',
                    'is_active', 'created_at')
    list_filter = ('category', 'form_type', 'route_type', 'is_active')
    search_fields = ('code', 'name')
    filter_horizontal = ('allowed_departments', 'allowed_duties', 'allowed_positions')
    inlines = [ApprovalPolicyRuleInline, RouteTemplateInline]


class ApprovalStepInline(admin.TabularInline):
    model = ApprovalStep
    extra = 0
    readonly_fields = ('step_order', 'role_label', 'condition', 'status')
    filter_horizontal = ('approvers',)


class ApprovalActionInline(admin.TabularInline):
    model = ApprovalAction
    extra = 0
    readonly_fields = ('approver', 'action', 'comment', 'content_hash', 'acted_at')
    fk_name = 'step'


class ApprovalAttachmentInline(admin.TabularInline):
    model = ApprovalAttachment
    extra = 0
    readonly_fields = ('file_name', 'file_type', 'file_size', 'created_at', 'creator')


@admin.register(ApprovalDocument)
class ApprovalDocumentAdmin(admin.ModelAdmin):
    list_display = ('doc_number', 'title', 'doc_type', 'drafter', 'status', 'created_at')
    list_filter = ('status', 'doc_type')
    search_fields = ('title', 'drafter__username', 'doc_number')
    readonly_fields = ('doc_number', 'content_hash', 'created_at', 'updated_at', 'submitted_at', 'completed_at')
    filter_horizontal = ('observers',)
    inlines = [ApprovalAttachmentInline, ApprovalStepInline]


@admin.register(ApprovalAttachment)
class ApprovalAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'file_name', 'file_type', 'file_size', 'creator', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('file_name', 'document__title', 'document__doc_number')
