// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'common_models.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$SimpleUserModelImpl _$$SimpleUserModelImplFromJson(
  Map<String, dynamic> json,
) => _$SimpleUserModelImpl(
  pk: (_readPk(json, 'pk') as num).toInt(),
  username: json['username'] as String? ?? '',
  email: json['email'] as String?,
  fullName: json['full_name'] as String?,
);

Map<String, dynamic> _$$SimpleUserModelImplToJson(
  _$SimpleUserModelImpl instance,
) => <String, dynamic>{
  'pk': instance.pk,
  'username': instance.username,
  'email': instance.email,
  'full_name': instance.fullName,
};

_$SimpleProjectModelImpl _$$SimpleProjectModelImplFromJson(
  Map<String, dynamic> json,
) => _$SimpleProjectModelImpl(
  pk: (_readPk(json, 'pk') as num).toInt(),
  name: json['name'] as String? ?? '',
  slug: json['slug'] as String? ?? '',
);

Map<String, dynamic> _$$SimpleProjectModelImplToJson(
  _$SimpleProjectModelImpl instance,
) => <String, dynamic>{
  'pk': instance.pk,
  'name': instance.name,
  'slug': instance.slug,
};
