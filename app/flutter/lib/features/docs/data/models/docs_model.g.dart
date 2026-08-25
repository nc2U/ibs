// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'docs_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$DocCategoryModelImpl _$$DocCategoryModelImplFromJson(
  Map<String, dynamic> json,
) => _$DocCategoryModelImpl(
  pk: (json['pk'] as num).toInt(),
  docType: json['doc_type'] as String?,
  color: json['color'] as String?,
  name: json['name'] as String,
  parent: (json['parent'] as num?)?.toInt(),
  order: (json['order'] as num?)?.toInt() ?? 0,
  active: json['active'] as bool? ?? true,
  defaultVal: json['default_val'] as bool? ?? false,
);

Map<String, dynamic> _$$DocCategoryModelImplToJson(
  _$DocCategoryModelImpl instance,
) => <String, dynamic>{
  'pk': instance.pk,
  'doc_type': instance.docType,
  'color': instance.color,
  'name': instance.name,
  'parent': instance.parent,
  'order': instance.order,
  'active': instance.active,
  'default_val': instance.defaultVal,
};

_$DocFileModelImpl _$$DocFileModelImplFromJson(Map<String, dynamic> json) =>
    _$DocFileModelImpl(
      pk: (json['pk'] as num).toInt(),
      docs: (json['docs'] as num?)?.toInt(),
      fileName: json['file_name'] as String?,
      file: json['file'] as String?,
      fileType: json['file_type'] as String?,
      fileSize: (json['file_size'] as num?)?.toInt(),
      description: json['description'] as String?,
      creator: json['creator'] as String?,
      hit: (json['hit'] as num?)?.toInt() ?? 0,
      created: json['created'] as String?,
    );

Map<String, dynamic> _$$DocFileModelImplToJson(_$DocFileModelImpl instance) =>
    <String, dynamic>{
      'pk': instance.pk,
      'docs': instance.docs,
      'file_name': instance.fileName,
      'file': instance.file,
      'file_type': instance.fileType,
      'file_size': instance.fileSize,
      'description': instance.description,
      'creator': instance.creator,
      'hit': instance.hit,
      'created': instance.created,
    };

_$DocLinkModelImpl _$$DocLinkModelImplFromJson(Map<String, dynamic> json) =>
    _$DocLinkModelImpl(
      pk: (json['pk'] as num).toInt(),
      docs: (json['docs'] as num?)?.toInt(),
      link: json['link'] as String,
      description: json['description'] as String?,
      creator: json['creator'] as String?,
      hit: (json['hit'] as num?)?.toInt() ?? 0,
      created: json['created'] as String?,
    );

Map<String, dynamic> _$$DocLinkModelImplToJson(_$DocLinkModelImpl instance) =>
    <String, dynamic>{
      'pk': instance.pk,
      'docs': instance.docs,
      'link': instance.link,
      'description': instance.description,
      'creator': instance.creator,
      'hit': instance.hit,
      'created': instance.created,
    };

_$DocumentModelImpl _$$DocumentModelImplFromJson(Map<String, dynamic> json) =>
    _$DocumentModelImpl(
      pk: (json['pk'] as num).toInt(),
      project: json['project'] == null
          ? null
          : SimpleProjectModel.fromJson(
              json['project'] as Map<String, dynamic>,
            ),
      projType: json['proj_type'] as String?,
      docType: json['doc_type'] as String?,
      typeName: json['type_name'] as String?,
      category: (json['category'] as num?)?.toInt(),
      cateName: json['cate_name'] as String?,
      cateColor: json['cate_color'] as String?,
      lawsuit: (json['lawsuit'] as num?)?.toInt(),
      lawsuitName: json['lawsuit_name'] as String?,
      title: json['title'] as String,
      executionDate: json['execution_date'] as String?,
      description: json['description'] as String? ?? '',
      hit: (json['hit'] as num?)?.toInt() ?? 0,
      isPinned: json['is_pinned'] as bool? ?? false,
      securityLevel: json['security_level'] as String? ?? '3',
      securityLevelDesc: json['security_level_desc'] as String?,
      creatorDeptName: json['creator_dept_name'] as String?,
      allowedUsers:
          (json['allowed_users'] as List<dynamic>?)
              ?.map((e) => (e as num).toInt())
              .toList() ??
          const [],
      isBlind: json['is_blind'] as bool? ?? false,
      files:
          (json['files'] as List<dynamic>?)
              ?.map((e) => DocFileModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      links:
          (json['links'] as List<dynamic>?)
              ?.map((e) => DocLinkModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      creator: json['creator'] == null
          ? null
          : SimpleUserModel.fromJson(json['creator'] as Map<String, dynamic>),
      updator: json['updator'] == null
          ? null
          : SimpleUserModel.fromJson(json['updator'] as Map<String, dynamic>),
      created: json['created'] as String?,
      updated: json['updated'] as String?,
      isNew: json['is_new'] as bool? ?? false,
    );

Map<String, dynamic> _$$DocumentModelImplToJson(_$DocumentModelImpl instance) =>
    <String, dynamic>{
      'pk': instance.pk,
      'project': instance.project,
      'proj_type': instance.projType,
      'doc_type': instance.docType,
      'type_name': instance.typeName,
      'category': instance.category,
      'cate_name': instance.cateName,
      'cate_color': instance.cateColor,
      'lawsuit': instance.lawsuit,
      'lawsuit_name': instance.lawsuitName,
      'title': instance.title,
      'execution_date': instance.executionDate,
      'description': instance.description,
      'hit': instance.hit,
      'is_pinned': instance.isPinned,
      'security_level': instance.securityLevel,
      'security_level_desc': instance.securityLevelDesc,
      'creator_dept_name': instance.creatorDeptName,
      'allowed_users': instance.allowedUsers,
      'is_blind': instance.isBlind,
      'files': instance.files,
      'links': instance.links,
      'creator': instance.creator,
      'updator': instance.updator,
      'created': instance.created,
      'updated': instance.updated,
      'is_new': instance.isNew,
    };

_$DocumentListResponseModelImpl _$$DocumentListResponseModelImplFromJson(
  Map<String, dynamic> json,
) => _$DocumentListResponseModelImpl(
  count: (json['count'] as num).toInt(),
  next: json['next'] as String?,
  previous: json['previous'] as String?,
  results: (json['results'] as List<dynamic>)
      .map((e) => DocumentModel.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$$DocumentListResponseModelImplToJson(
  _$DocumentListResponseModelImpl instance,
) => <String, dynamic>{
  'count': instance.count,
  'next': instance.next,
  'previous': instance.previous,
  'results': instance.results,
};
