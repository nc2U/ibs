import 'package:freezed_annotation/freezed_annotation.dart';

part 'common_models.freezed.dart';
part 'common_models.g.dart';

@freezed
class SimpleUserModel with _$SimpleUserModel {
  const factory SimpleUserModel({
    required int pk,
    required String username,
    String? email,
  }) = _SimpleUserModel;

  factory SimpleUserModel.fromJson(Map<String, dynamic> json) =>
      _$SimpleUserModelFromJson(json);
}

@freezed
class SimpleProjectModel with _$SimpleProjectModel {
  const factory SimpleProjectModel({
    required int pk,
    required String name,
    required String slug,
  }) = _SimpleProjectModel;

  factory SimpleProjectModel.fromJson(Map<String, dynamic> json) =>
      _$SimpleProjectModelFromJson(json);
}
