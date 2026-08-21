import 'package:freezed_annotation/freezed_annotation.dart';

part 'common_models.freezed.dart';
part 'common_models.g.dart';

Object? _readPk(Map json, String key) {
  final val = json['pk'] ?? json['id'];
  if (val is num) return val.toInt();
  if (val is String) return int.tryParse(val) ?? 0;
  return 0;
}

@freezed
class SimpleUserModel with _$SimpleUserModel {
  const factory SimpleUserModel({
    @JsonKey(readValue: _readPk) required int pk,
    @Default('') String username,
    String? email,
    String? fullName,
  }) = _SimpleUserModel;

  factory SimpleUserModel.fromJson(Map<String, dynamic> json) =>
      _$SimpleUserModelFromJson(json);
}

@freezed
class SimpleProjectModel with _$SimpleProjectModel {
  const factory SimpleProjectModel({
    @JsonKey(readValue: _readPk) required int pk,
    @Default('') String name,
    @Default('') String slug,
  }) = _SimpleProjectModel;

  factory SimpleProjectModel.fromJson(Map<String, dynamic> json) =>
      _$SimpleProjectModelFromJson(json);
}
