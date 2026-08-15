import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../core/models/common_models.dart';

part 'docs_model.freezed.dart';
part 'docs_model.g.dart';

@freezed
class DocCategoryModel with _$DocCategoryModel {
  const factory DocCategoryModel({
    required int pk,
    String? docType,
    String? color,
    required String name,
    int? parent,
    @Default(0) int order,
    @Default(true) bool active,
    @Default(false) bool defaultVal,
  }) = _DocCategoryModel;

  factory DocCategoryModel.fromJson(Map<String, dynamic> json) =>
      _$DocCategoryModelFromJson(json);
}

@freezed
class DocFileModel with _$DocFileModel {
  const factory DocFileModel({
    required int pk,
    int? docs,
    String? fileName,
    String? file,
    String? fileType,
    int? fileSize,
    String? description,
    String? creator,
    @Default(0) int hit,
    String? created,
  }) = _DocFileModel;

  factory DocFileModel.fromJson(Map<String, dynamic> json) =>
      _$DocFileModelFromJson(json);
}

@freezed
class DocLinkModel with _$DocLinkModel {
  const factory DocLinkModel({
    required int pk,
    int? docs,
    required String link,
    String? description,
    String? creator,
    @Default(0) int hit,
    String? created,
  }) = _DocLinkModel;

  factory DocLinkModel.fromJson(Map<String, dynamic> json) =>
      _$DocLinkModelFromJson(json);
}

@freezed
class DocumentModel with _$DocumentModel {
  const factory DocumentModel({
    required int pk,
    SimpleProjectModel? project,
    String? projType,
    String? docType,
    String? typeName,
    int? category,
    String? cateName,
    String? cateColor,
    int? lawsuit,
    String? lawsuitName,
    required String title,
    String? executionDate,
    @Default('') String description,
    @Default(0) int hit,
    @Default(false) bool isPinned,
    @Default(false) bool isSecret,
    @Default(false) bool isBlind,
    @Default([]) List<DocFileModel> files,
    @Default([]) List<DocLinkModel> links,
    SimpleUserModel? creator,
    SimpleUserModel? updator,
    String? created,
    String? updated,
    @Default(false) bool isNew,
  }) = _DocumentModel;

  factory DocumentModel.fromJson(Map<String, dynamic> json) =>
      _$DocumentModelFromJson(json);
}

@freezed
class DocumentListResponseModel with _$DocumentListResponseModel {
  const factory DocumentListResponseModel({
    required int count,
    String? next,
    String? previous,
    required List<DocumentModel> results,
  }) = _DocumentListResponseModel;

  factory DocumentListResponseModel.fromJson(Map<String, dynamic> json) =>
      _$DocumentListResponseModelFromJson(json);
}

/// 소송 사건 옵션 모델 (드롭다운 바인딩용)
class SuitCaseOptionModel {
  final int pk;
  final String label;
  final String? caseNumber;
  final String? caseName;

  const SuitCaseOptionModel({
    required this.pk,
    required this.label,
    this.caseNumber,
    this.caseName,
  });

  factory SuitCaseOptionModel.fromJson(Map<String, dynamic> json) {
    final str = json['__str__']?.toString();
    final caseNum = json['case_number']?.toString();
    final caseName = json['case_name']?.toString();
    final fallbackLabel = (caseNum != null && caseName != null)
        ? '$caseNum $caseName'
        : '사건 #${json['pk'] ?? json['id']}';

    return SuitCaseOptionModel(
      pk: json['pk'] as int? ?? json['id'] as int? ?? 0,
      label: (str != null && str.isNotEmpty) ? str : fallbackLabel,
      caseNumber: caseNum,
      caseName: caseName,
    );
  }
}
