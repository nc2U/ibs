// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'approval_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$DocCategoryModelImpl _$$DocCategoryModelImplFromJson(
  Map<String, dynamic> json,
) => _$DocCategoryModelImpl(
  id: (_readId(json, 'id') as num).toInt(),
  name: _readStr(json, 'name') as String? ?? '',
  code: _readStr(json, 'code') as String? ?? '',
  description: json['description'] as String? ?? '',
  order: (json['order'] as num?)?.toInt() ?? 1,
  isActive: json['is_active'] as bool? ?? true,
);

Map<String, dynamic> _$$DocCategoryModelImplToJson(
  _$DocCategoryModelImpl instance,
) => <String, dynamic>{
  'id': instance.id,
  'name': instance.name,
  'code': instance.code,
  'description': instance.description,
  'order': instance.order,
  'is_active': instance.isActive,
};

_$FormFieldModelImpl _$$FormFieldModelImplFromJson(Map<String, dynamic> json) =>
    _$FormFieldModelImpl(
      key: json['key'] as String,
      label: json['label'] as String,
      type: json['type'] as String,
      required: json['required'] as bool? ?? false,
      options: (json['options'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
    );

Map<String, dynamic> _$$FormFieldModelImplToJson(
  _$FormFieldModelImpl instance,
) => <String, dynamic>{
  'key': instance.key,
  'label': instance.label,
  'type': instance.type,
  'required': instance.required,
  'options': instance.options,
};

_$DocumentTypeModelImpl _$$DocumentTypeModelImplFromJson(
  Map<String, dynamic> json,
) => _$DocumentTypeModelImpl(
  id: (_readId(json, 'id') as num).toInt(),
  name: _readStr(json, 'name') as String? ?? '',
  code: _readStr(json, 'code') as String? ?? '',
  description: json['description'] as String? ?? '',
  formTemplateKey: json['form_template_key'] as String? ?? 'GENERAL',
  routeType: json['route_type'] as String? ?? 'organization',
  category: (json['category'] as num?)?.toInt(),
  categoryName: json['category_name'] as String?,
  isActive: json['is_active'] as bool? ?? true,
);

Map<String, dynamic> _$$DocumentTypeModelImplToJson(
  _$DocumentTypeModelImpl instance,
) => <String, dynamic>{
  'id': instance.id,
  'name': instance.name,
  'code': instance.code,
  'description': instance.description,
  'form_template_key': instance.formTemplateKey,
  'route_type': instance.routeType,
  'category': instance.category,
  'category_name': instance.categoryName,
  'is_active': instance.isActive,
};

_$StaffAssignmentItemModelImpl _$$StaffAssignmentItemModelImplFromJson(
  Map<String, dynamic> json,
) => _$StaffAssignmentItemModelImpl(
  id: (_readId(json, 'id') as num).toInt(),
  company: (_readCompanyId(json, 'company') as num?)?.toInt(),
  companyName: _readCompanyName(json, 'company_name') as String?,
  department: (json['department'] as num?)?.toInt(),
  departmentName: json['department_name'] as String?,
  duty: (json['duty'] as num?)?.toInt(),
  dutyName: json['duty_name'] as String?,
  position: (json['position'] as num?)?.toInt(),
  positionName: json['position_name'] as String?,
  assignedTasks: _readDesc(json, 'assigned_tasks') as String?,
  isPrimary: json['is_primary'] as bool? ?? false,
);

Map<String, dynamic> _$$StaffAssignmentItemModelImplToJson(
  _$StaffAssignmentItemModelImpl instance,
) => <String, dynamic>{
  'id': instance.id,
  'company': instance.company,
  'company_name': instance.companyName,
  'department': instance.department,
  'department_name': instance.departmentName,
  'duty': instance.duty,
  'duty_name': instance.dutyName,
  'position': instance.position,
  'position_name': instance.positionName,
  'assigned_tasks': instance.assignedTasks,
  'is_primary': instance.isPrimary,
};

_$ApprovalActionModelImpl _$$ApprovalActionModelImplFromJson(
  Map<String, dynamic> json,
) => _$ApprovalActionModelImpl(
  id: (_readId(json, 'id') as num).toInt(),
  approver: SimpleUserModel.fromJson(json['approver'] as Map<String, dynamic>),
  action: _readStr(json, 'action') as String? ?? 'approved',
  comment: _readStr(json, 'comment') as String? ?? '',
  contentHash: _readStr(json, 'content_hash') as String? ?? '',
  actedAt: _readStr(json, 'acted_at') as String? ?? '',
);

Map<String, dynamic> _$$ApprovalActionModelImplToJson(
  _$ApprovalActionModelImpl instance,
) => <String, dynamic>{
  'id': instance.id,
  'approver': instance.approver,
  'action': instance.action,
  'comment': instance.comment,
  'content_hash': instance.contentHash,
  'acted_at': instance.actedAt,
};

_$ApprovalAttachmentModelImpl _$$ApprovalAttachmentModelImplFromJson(
  Map<String, dynamic> json,
) => _$ApprovalAttachmentModelImpl(
  id: (_readId(json, 'id') as num).toInt(),
  document: (_readId(json, 'document') as num).toInt(),
  file: json['file'] as String?,
  fileUrl: json['file_url'] as String?,
  fileName: _readStr(json, 'file_name') as String? ?? '',
  fileType: _readStr(json, 'file_type') as String? ?? '',
  fileSize: (json['file_size'] as num?)?.toInt(),
  creatorName: json['creator_name'] as String?,
  createdAt: _readStr(json, 'created_at') as String? ?? '',
);

Map<String, dynamic> _$$ApprovalAttachmentModelImplToJson(
  _$ApprovalAttachmentModelImpl instance,
) => <String, dynamic>{
  'id': instance.id,
  'document': instance.document,
  'file': instance.file,
  'file_url': instance.fileUrl,
  'file_name': instance.fileName,
  'file_type': instance.fileType,
  'file_size': instance.fileSize,
  'creator_name': instance.creatorName,
  'created_at': instance.createdAt,
};

_$ApprovalStepModelImpl _$$ApprovalStepModelImplFromJson(
  Map<String, dynamic> json,
) => _$ApprovalStepModelImpl(
  id: (_readId(json, 'id') as num).toInt(),
  stepOrder: (json['step_order'] as num).toInt(),
  roleLabel: _readStr(json, 'role_label') as String? ?? '',
  approvers:
      (json['approvers'] as List<dynamic>?)
          ?.map((e) => SimpleUserModel.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  condition: _readStr(json, 'condition') as String? ?? 'AND',
  status: _readStr(json, 'status') as String? ?? 'pending',
  actions:
      (json['actions'] as List<dynamic>?)
          ?.map((e) => ApprovalActionModel.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
);

Map<String, dynamic> _$$ApprovalStepModelImplToJson(
  _$ApprovalStepModelImpl instance,
) => <String, dynamic>{
  'id': instance.id,
  'step_order': instance.stepOrder,
  'role_label': instance.roleLabel,
  'approvers': instance.approvers,
  'condition': instance.condition,
  'status': instance.status,
  'actions': instance.actions,
};

_$RoutePreviewStepModelImpl _$$RoutePreviewStepModelImplFromJson(
  Map<String, dynamic> json,
) => _$RoutePreviewStepModelImpl(
  stepOrder: (json['step_order'] as num).toInt(),
  roleLabel: _readStr(json, 'role_label') as String? ?? '',
  approvers:
      (json['approvers'] as List<dynamic>?)
          ?.map((e) => SimpleUserModel.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  approverIds:
      (json['approver_ids'] as List<dynamic>?)
          ?.map((e) => (e as num).toInt())
          .toList() ??
      const [],
  condition: _readStr(json, 'condition') as String? ?? 'AND',
);

Map<String, dynamic> _$$RoutePreviewStepModelImplToJson(
  _$RoutePreviewStepModelImpl instance,
) => <String, dynamic>{
  'step_order': instance.stepOrder,
  'role_label': instance.roleLabel,
  'approvers': instance.approvers,
  'approver_ids': instance.approverIds,
  'condition': instance.condition,
};

_$ApprovalDocumentModelImpl _$$ApprovalDocumentModelImplFromJson(
  Map<String, dynamic> json,
) => _$ApprovalDocumentModelImpl(
  id: (_readId(json, 'id') as num).toInt(),
  docNumber: _readStr(json, 'doc_number') as String? ?? '',
  title: _readStr(json, 'title') as String? ?? '',
  docType: (_readDocTypeId(json, 'doc_type') as num).toInt(),
  docTypeName: json['doc_type_name'] as String?,
  categoryName: json['category_name'] as String?,
  docTypeDetail: json['doc_type_detail'] == null
      ? null
      : DocumentTypeModel.fromJson(
          json['doc_type_detail'] as Map<String, dynamic>,
        ),
  drafter: SimpleUserModel.fromJson(json['drafter'] as Map<String, dynamic>),
  drafterName: json['drafter_name'] as String?,
  drafterAssignment: (json['drafter_assignment'] as num?)?.toInt(),
  departmentName: json['department_name'] as String?,
  drafterAssignmentDesc: json['drafter_assignment_desc'] as String?,
  content: json['content'] as Map<String, dynamic>? ?? const {},
  status: _readStr(json, 'status') as String? ?? 'draft',
  statusDesc: json['status_desc'] as String?,
  currentStep: (json['current_step'] as num?)?.toInt() ?? 1,
  contentHash: _readStr(json, 'content_hash') as String? ?? '',
  pdfUrl: json['pdf_url'] as String?,
  attachmentCount: (json['attachment_count'] as num?)?.toInt() ?? 0,
  observerCount: (json['observer_count'] as num?)?.toInt() ?? 0,
  attachments: (json['attachments'] as List<dynamic>?)
      ?.map((e) => ApprovalAttachmentModel.fromJson(e as Map<String, dynamic>))
      .toList(),
  observers: (json['observers'] as List<dynamic>?)
      ?.map((e) => SimpleUserModel.fromJson(e as Map<String, dynamic>))
      .toList(),
  steps: (json['steps'] as List<dynamic>?)
      ?.map((e) => ApprovalStepModel.fromJson(e as Map<String, dynamic>))
      .toList(),
  createdAt: _readStr(json, 'created_at') as String? ?? '',
  submittedAt: json['submitted_at'] as String?,
  completedAt: json['completed_at'] as String?,
);

Map<String, dynamic> _$$ApprovalDocumentModelImplToJson(
  _$ApprovalDocumentModelImpl instance,
) => <String, dynamic>{
  'id': instance.id,
  'doc_number': instance.docNumber,
  'title': instance.title,
  'doc_type': instance.docType,
  'doc_type_name': instance.docTypeName,
  'category_name': instance.categoryName,
  'doc_type_detail': instance.docTypeDetail,
  'drafter': instance.drafter,
  'drafter_name': instance.drafterName,
  'drafter_assignment': instance.drafterAssignment,
  'department_name': instance.departmentName,
  'drafter_assignment_desc': instance.drafterAssignmentDesc,
  'content': instance.content,
  'status': instance.status,
  'status_desc': instance.statusDesc,
  'current_step': instance.currentStep,
  'content_hash': instance.contentHash,
  'pdf_url': instance.pdfUrl,
  'attachment_count': instance.attachmentCount,
  'observer_count': instance.observerCount,
  'attachments': instance.attachments,
  'observers': instance.observers,
  'steps': instance.steps,
  'created_at': instance.createdAt,
  'submitted_at': instance.submittedAt,
  'completed_at': instance.completedAt,
};

_$ApprovalDocumentListResponseImpl _$$ApprovalDocumentListResponseImplFromJson(
  Map<String, dynamic> json,
) => _$ApprovalDocumentListResponseImpl(
  count: (json['count'] as num?)?.toInt() ?? 0,
  next: json['next'] as String?,
  previous: json['previous'] as String?,
  results:
      (json['results'] as List<dynamic>?)
          ?.map(
            (e) => ApprovalDocumentModel.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$$ApprovalDocumentListResponseImplToJson(
  _$ApprovalDocumentListResponseImpl instance,
) => <String, dynamic>{
  'count': instance.count,
  'next': instance.next,
  'previous': instance.previous,
  'results': instance.results,
};
