import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../core/models/common_models.dart';

part 'approval_model.freezed.dart';
part 'approval_model.g.dart';

Object? _readId(Map json, String key) {
  final val = json['id'] ?? json['pk'];
  if (val is num) return val.toInt();
  if (val is String) return int.tryParse(val) ?? 0;
  return 0;
}

Object? _readCompanyId(Map json, String key) {
  final val = json['company'];
  if (val is num) return val.toInt();
  final valId = json['company_id'];
  if (valId is num) return valId.toInt();
  return null;
}

Object? _readCompanyName(Map json, String key) {
  if (json['company_name'] != null) return json['company_name'].toString();
  if (json['company'] is String) return json['company'] as String;
  return null;
}

Object? _readDesc(Map json, String key) =>
    (json['assigned_tasks'] ?? json['desc'])?.toString();

Object? _readDocTypeId(Map json, String key) {
  final val = json['doc_type'];
  if (val is num) return val.toInt();
  if (val is Map) {
    final subId = val['id'] ?? val['pk'];
    if (subId is num) return subId.toInt();
  }
  if (val is String) return int.tryParse(val) ?? 0;
  return 0;
}

// ── 0. 결재 카테고리 모델 ──────────────────────────────────────────
@freezed
class DocCategoryModel with _$DocCategoryModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory DocCategoryModel({
    @JsonKey(readValue: _readId) required int id,
    required String name,
    required String code,
    @Default('') String description,
    @Default(1) int order,
    @Default(true) bool isActive,
  }) = _DocCategoryModel;

  factory DocCategoryModel.fromJson(Map<String, dynamic> json) =>
      _$DocCategoryModelFromJson(json);
}

// ── 1. 동적 폼 필드 모델 ──────────────────────────────────────────
@freezed
class FormFieldModel with _$FormFieldModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory FormFieldModel({
    required String key,
    required String label,
    required String type, // text, textarea, number, date, select
    @Default(false) bool required,
    List<String>? options,
  }) = _FormFieldModel;

  factory FormFieldModel.fromJson(Map<String, dynamic> json) =>
      _$FormFieldModelFromJson(json);
}

// ── 2. 문서 유형 모델 ─────────────────────────────────────────────
@freezed
class DocumentTypeModel with _$DocumentTypeModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory DocumentTypeModel({
    @JsonKey(readValue: _readId) required int id,
    required String name,
    required String code,
    @Default('') String description,
    @Default('GENERAL') String formTemplateKey,
    @Default('organization') String routeType,
    int? category,
    String? categoryName,
    @Default(true) bool isActive,
  }) = _DocumentTypeModel;

  factory DocumentTypeModel.fromJson(Map<String, dynamic> json) =>
      _$DocumentTypeModelFromJson(json);
}

// ── 3. 기안자 보직/겸직 모델 ───────────────────────────────────────
@freezed
class StaffAssignmentItemModel with _$StaffAssignmentItemModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory StaffAssignmentItemModel({
    @JsonKey(readValue: _readId) required int id,
    @JsonKey(readValue: _readCompanyId) int? company,
    @JsonKey(readValue: _readCompanyName) String? companyName,
    int? department,
    String? departmentName,
    int? duty,
    String? dutyName,
    int? position,
    String? positionName,
    @JsonKey(readValue: _readDesc) String? assignedTasks,
    @Default(false) bool isPrimary,
  }) = _StaffAssignmentItemModel;

  factory StaffAssignmentItemModel.fromJson(Map<String, dynamic> json) =>
      _$StaffAssignmentItemModelFromJson(json);
}

// ── 4. 결재 행동 이력 모델 ─────────────────────────────────────────
@freezed
class ApprovalActionModel with _$ApprovalActionModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory ApprovalActionModel({
    @JsonKey(readValue: _readId) required int id,
    required SimpleUserModel approver,
    required String action, // approved, rejected, commented
    @Default('') String comment,
    @Default('') String contentHash,
    required String actedAt,
  }) = _ApprovalActionModel;

  factory ApprovalActionModel.fromJson(Map<String, dynamic> json) =>
      _$ApprovalActionModelFromJson(json);
}

// ── 5. 결재 첨부파일 모델 ──────────────────────────────────────────
@freezed
class ApprovalAttachmentModel with _$ApprovalAttachmentModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory ApprovalAttachmentModel({
    @JsonKey(readValue: _readId) required int id,
    @JsonKey(readValue: _readId) required int document,
    String? file,
    String? fileUrl,
    @Default('') String fileName,
    @Default('') String fileType,
    int? fileSize,
    String? creatorName,
    required String createdAt,
  }) = _ApprovalAttachmentModel;

  factory ApprovalAttachmentModel.fromJson(Map<String, dynamic> json) =>
      _$ApprovalAttachmentModelFromJson(json);
}

// ── 6. 결재 단계 모델 ─────────────────────────────────────────────
@freezed
class ApprovalStepModel with _$ApprovalStepModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory ApprovalStepModel({
    @JsonKey(readValue: _readId) required int id,
    required int stepOrder,
    required String roleLabel,
    @Default([]) List<SimpleUserModel> approvers,
    @Default('AND') String condition, // AND, OR
    @Default('pending') String status, // pending, approved, rejected, skipped
    @Default([]) List<ApprovalActionModel> actions,
  }) = _ApprovalStepModel;

  factory ApprovalStepModel.fromJson(Map<String, dynamic> json) =>
      _$ApprovalStepModelFromJson(json);
}

// ── 7. 결재선 미리보기 모델 ────────────────────────────────────────
@freezed
class RoutePreviewStepModel with _$RoutePreviewStepModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory RoutePreviewStepModel({
    required int stepOrder,
    required String roleLabel,
    @Default([]) List<SimpleUserModel> approvers,
    @Default([]) List<int> approverIds,
    @Default('AND') String condition,
  }) = _RoutePreviewStepModel;

  factory RoutePreviewStepModel.fromJson(Map<String, dynamic> json) =>
      _$RoutePreviewStepModelFromJson(json);
}

// ── 8. 결재 문서 상세 및 목록 모델 ──────────────────────────────────
@freezed
class ApprovalDocumentModel with _$ApprovalDocumentModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory ApprovalDocumentModel({
    @JsonKey(readValue: _readId) required int id,
    @Default('') String docNumber,
    required String title,
    @JsonKey(readValue: _readDocTypeId) required int docType,
    String? docTypeName,
    String? categoryName,
    DocumentTypeModel? docTypeDetail,
    required SimpleUserModel drafter,
    String? drafterName,
    int? drafterAssignment,
    String? departmentName,
    String? drafterAssignmentDesc,
    @Default({}) Map<String, dynamic> content,
    @Default('draft') String status, // draft, pending, approved, rejected, cancelled
    String? statusDesc,
    @Default(1) int currentStep,
    @Default('') String contentHash,
    String? pdfUrl,
    @Default(0) int attachmentCount,
    @Default(0) int observerCount,
    List<ApprovalAttachmentModel>? attachments,
    List<SimpleUserModel>? observers,
    List<ApprovalStepModel>? steps,
    required String createdAt,
    String? submittedAt,
    String? completedAt,
  }) = _ApprovalDocumentModel;

  factory ApprovalDocumentModel.fromJson(Map<String, dynamic> json) =>
      _$ApprovalDocumentModelFromJson(json);
}

// ── 9. 결재 문서 페이지네이션 응답 모델 ──────────────────────────────
@freezed
class ApprovalDocumentListResponse with _$ApprovalDocumentListResponse {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory ApprovalDocumentListResponse({
    @Default(0) int count,
    String? next,
    String? previous,
    @Default([]) List<ApprovalDocumentModel> results,
  }) = _ApprovalDocumentListResponse;

  factory ApprovalDocumentListResponse.fromJson(Map<String, dynamic> json) =>
      _$ApprovalDocumentListResponseFromJson(json);
}
