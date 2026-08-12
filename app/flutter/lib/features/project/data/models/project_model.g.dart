// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'project_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$ProjectModelImpl _$$ProjectModelImplFromJson(Map<String, dynamic> json) =>
    _$ProjectModelImpl(
      pk: (json['pk'] as num).toInt(),
      name: json['name'] as String,
      slug: json['slug'] as String,
      description: json['description'] as String? ?? '',
      status: json['status'] as String? ?? '1',
      visible: json['visible'] as bool? ?? true,
      isBookmarked: json['is_bookmarked'] as bool? ?? false,
    );

Map<String, dynamic> _$$ProjectModelImplToJson(_$ProjectModelImpl instance) =>
    <String, dynamic>{
      'pk': instance.pk,
      'name': instance.name,
      'slug': instance.slug,
      'description': instance.description,
      'status': instance.status,
      'visible': instance.visible,
      'is_bookmarked': instance.isBookmarked,
    };

_$ProjectListResponseImpl _$$ProjectListResponseImplFromJson(
  Map<String, dynamic> json,
) => _$ProjectListResponseImpl(
  count: (json['count'] as num).toInt(),
  next: json['next'] as String?,
  previous: json['previous'] as String?,
  results: (json['results'] as List<dynamic>)
      .map((e) => ProjectModel.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$$ProjectListResponseImplToJson(
  _$ProjectListResponseImpl instance,
) => <String, dynamic>{
  'count': instance.count,
  'next': instance.next,
  'previous': instance.previous,
  'results': instance.results,
};
