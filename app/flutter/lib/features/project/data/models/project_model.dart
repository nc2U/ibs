import 'package:freezed_annotation/freezed_annotation.dart';

part 'project_model.freezed.dart';
part 'project_model.g.dart';

@freezed
class ProjectModel with _$ProjectModel {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory ProjectModel({
    required int pk,
    required String name,
    required String slug,
    @Default('') String description,
    @Default('1') String status,
    @Default(true) bool visible,
    @Default(false) bool isBookmarked,
  }) = _ProjectModel;

  factory ProjectModel.fromJson(Map<String, dynamic> json) =>
      _$ProjectModelFromJson(json);
}

@freezed
class ProjectListResponse with _$ProjectListResponse {
  @JsonSerializable(fieldRename: FieldRename.snake)
  const factory ProjectListResponse({
    required int count,
    String? next,
    String? previous,
    required List<ProjectModel> results,
  }) = _ProjectListResponse;

  factory ProjectListResponse.fromJson(Map<String, dynamic> json) =>
      _$ProjectListResponseFromJson(json);
}
