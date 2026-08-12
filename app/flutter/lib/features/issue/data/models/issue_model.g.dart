// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'issue_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$IssueStatusModelImpl _$$IssueStatusModelImplFromJson(
  Map<String, dynamic> json,
) => _$IssueStatusModelImpl(
  pk: (json['pk'] as num).toInt(),
  name: json['name'] as String,
  closed: json['closed'] as bool,
);

Map<String, dynamic> _$$IssueStatusModelImplToJson(
  _$IssueStatusModelImpl instance,
) => <String, dynamic>{
  'pk': instance.pk,
  'name': instance.name,
  'closed': instance.closed,
};

_$IssuePriorityModelImpl _$$IssuePriorityModelImplFromJson(
  Map<String, dynamic> json,
) => _$IssuePriorityModelImpl(
  pk: (json['pk'] as num).toInt(),
  name: json['name'] as String,
);

Map<String, dynamic> _$$IssuePriorityModelImplToJson(
  _$IssuePriorityModelImpl instance,
) => <String, dynamic>{'pk': instance.pk, 'name': instance.name};

_$IssueTrackerModelImpl _$$IssueTrackerModelImplFromJson(
  Map<String, dynamic> json,
) => _$IssueTrackerModelImpl(
  pk: (json['pk'] as num).toInt(),
  name: json['name'] as String,
  description: json['description'] as String? ?? '',
);

Map<String, dynamic> _$$IssueTrackerModelImplToJson(
  _$IssueTrackerModelImpl instance,
) => <String, dynamic>{
  'pk': instance.pk,
  'name': instance.name,
  'description': instance.description,
};

_$IssueVersionModelImpl _$$IssueVersionModelImplFromJson(
  Map<String, dynamic> json,
) => _$IssueVersionModelImpl(
  pk: (json['pk'] as num).toInt(),
  name: json['name'] as String,
  description: json['description'] as String? ?? '',
);

Map<String, dynamic> _$$IssueVersionModelImplToJson(
  _$IssueVersionModelImpl instance,
) => <String, dynamic>{
  'pk': instance.pk,
  'name': instance.name,
  'description': instance.description,
};

_$MeetingDescModelImpl _$$MeetingDescModelImplFromJson(
  Map<String, dynamic> json,
) => _$MeetingDescModelImpl(
  pk: (json['pk'] as num).toInt(),
  title: json['title'] as String,
);

Map<String, dynamic> _$$MeetingDescModelImplToJson(
  _$MeetingDescModelImpl instance,
) => <String, dynamic>{'pk': instance.pk, 'title': instance.title};

_$ParentIssueModelImpl _$$ParentIssueModelImplFromJson(
  Map<String, dynamic> json,
) => _$ParentIssueModelImpl(
  pk: (json['pk'] as num).toInt(),
  tracker: json['tracker'] as String,
  subject: json['subject'] as String,
  isPrivate: json['isPrivate'] as bool? ?? false,
);

Map<String, dynamic> _$$ParentIssueModelImplToJson(
  _$ParentIssueModelImpl instance,
) => <String, dynamic>{
  'pk': instance.pk,
  'tracker': instance.tracker,
  'subject': instance.subject,
  'isPrivate': instance.isPrivate,
};

_$IssueFileModelImpl _$$IssueFileModelImplFromJson(Map<String, dynamic> json) =>
    _$IssueFileModelImpl(
      pk: (json['pk'] as num).toInt(),
      file: json['file'] as String,
      fileName: json['fileName'] as String,
      fileType: json['fileType'] as String? ?? '',
      fileSize: (json['fileSize'] as num?)?.toInt(),
      description: json['description'] as String? ?? '',
      created: json['created'] as String,
      creator: json['creator'] == null
          ? null
          : SimpleUserModel.fromJson(json['creator'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$IssueFileModelImplToJson(
  _$IssueFileModelImpl instance,
) => <String, dynamic>{
  'pk': instance.pk,
  'file': instance.file,
  'fileName': instance.fileName,
  'fileType': instance.fileType,
  'fileSize': instance.fileSize,
  'description': instance.description,
  'created': instance.created,
  'creator': instance.creator,
};

_$IssueLinkModelImpl _$$IssueLinkModelImplFromJson(Map<String, dynamic> json) =>
    _$IssueLinkModelImpl(
      pk: (json['pk'] as num).toInt(),
      link: json['link'] as String,
      name: json['name'] as String,
      hit: (json['hit'] as num?)?.toInt() ?? 0,
      created: json['created'] as String,
      creator: json['creator'] == null
          ? null
          : SimpleUserModel.fromJson(json['creator'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$IssueLinkModelImplToJson(
  _$IssueLinkModelImpl instance,
) => <String, dynamic>{
  'pk': instance.pk,
  'link': instance.link,
  'name': instance.name,
  'hit': instance.hit,
  'created': instance.created,
  'creator': instance.creator,
};

_$SubIssueModelImpl _$$SubIssueModelImplFromJson(
  Map<String, dynamic> json,
) => _$SubIssueModelImpl(
  pk: (json['pk'] as num).toInt(),
  project: SimpleProjectModel.fromJson(json['project'] as Map<String, dynamic>),
  subject: json['subject'] as String,
  tracker: IssueTrackerModel.fromJson(json['tracker'] as Map<String, dynamic>),
  status: json['status'] as String,
  assignedTo: json['assignedTo'] == null
      ? null
      : SimpleUserModel.fromJson(json['assignedTo'] as Map<String, dynamic>),
  watchers:
      (json['watchers'] as List<dynamic>?)
          ?.map((e) => SimpleUserModel.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  priority: (json['priority'] as num?)?.toInt(),
  startDate: json['startDate'] as String?,
  dueDate: json['dueDate'] as String?,
  doneRatio: (json['doneRatio'] as num?)?.toInt() ?? 0,
  closed: json['closed'] as String?,
);

Map<String, dynamic> _$$SubIssueModelImplToJson(_$SubIssueModelImpl instance) =>
    <String, dynamic>{
      'pk': instance.pk,
      'project': instance.project,
      'subject': instance.subject,
      'tracker': instance.tracker,
      'status': instance.status,
      'assignedTo': instance.assignedTo,
      'watchers': instance.watchers,
      'priority': instance.priority,
      'startDate': instance.startDate,
      'dueDate': instance.dueDate,
      'doneRatio': instance.doneRatio,
      'closed': instance.closed,
    };

_$IssueInRelationModelImpl _$$IssueInRelationModelImplFromJson(
  Map<String, dynamic> json,
) => _$IssueInRelationModelImpl(
  pk: (json['pk'] as num).toInt(),
  project: SimpleProjectModel.fromJson(json['project'] as Map<String, dynamic>),
  subject: json['subject'] as String,
  tracker: IssueTrackerModel.fromJson(json['tracker'] as Map<String, dynamic>),
  status: json['status'] as String,
  assignedTo: json['assignedTo'] == null
      ? null
      : SimpleUserModel.fromJson(json['assignedTo'] as Map<String, dynamic>),
  watchers:
      (json['watchers'] as List<dynamic>?)
          ?.map((e) => SimpleUserModel.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  priority: (json['priority'] as num?)?.toInt(),
  startDate: json['startDate'] as String?,
  dueDate: json['dueDate'] as String?,
  doneRatio: (json['doneRatio'] as num?)?.toInt() ?? 0,
  closed: json['closed'] as String?,
);

Map<String, dynamic> _$$IssueInRelationModelImplToJson(
  _$IssueInRelationModelImpl instance,
) => <String, dynamic>{
  'pk': instance.pk,
  'project': instance.project,
  'subject': instance.subject,
  'tracker': instance.tracker,
  'status': instance.status,
  'assignedTo': instance.assignedTo,
  'watchers': instance.watchers,
  'priority': instance.priority,
  'startDate': instance.startDate,
  'dueDate': instance.dueDate,
  'doneRatio': instance.doneRatio,
  'closed': instance.closed,
};

_$IssueRelationModelImpl _$$IssueRelationModelImplFromJson(
  Map<String, dynamic> json,
) => _$IssueRelationModelImpl(
  pk: (json['pk'] as num?)?.toInt(),
  issue: json['issue'] == null
      ? null
      : IssueInRelationModel.fromJson(json['issue'] as Map<String, dynamic>),
  delay: (json['delay'] as num?)?.toInt(),
);

Map<String, dynamic> _$$IssueRelationModelImplToJson(
  _$IssueRelationModelImpl instance,
) => <String, dynamic>{
  'pk': instance.pk,
  'issue': instance.issue,
  'delay': instance.delay,
};

_$IssueCommentModelImpl _$$IssueCommentModelImplFromJson(
  Map<String, dynamic> json,
) => _$IssueCommentModelImpl(
  pk: (json['pk'] as num).toInt(),
  content: json['content'] as String,
  isPrivate: json['isPrivate'] as bool? ?? false,
  isBlocked: json['isBlocked'] as bool? ?? false,
  created: json['created'] as String,
  updated: json['updated'] as String,
  creator: SimpleUserModel.fromJson(json['creator'] as Map<String, dynamic>),
);

Map<String, dynamic> _$$IssueCommentModelImplToJson(
  _$IssueCommentModelImpl instance,
) => <String, dynamic>{
  'pk': instance.pk,
  'content': instance.content,
  'isPrivate': instance.isPrivate,
  'isBlocked': instance.isBlocked,
  'created': instance.created,
  'updated': instance.updated,
  'creator': instance.creator,
};

_$IssueModelImpl _$$IssueModelImplFromJson(
  Map<String, dynamic> json,
) => _$IssueModelImpl(
  pk: (json['pk'] as num).toInt(),
  project: SimpleProjectModel.fromJson(json['project'] as Map<String, dynamic>),
  tracker: IssueTrackerModel.fromJson(json['tracker'] as Map<String, dynamic>),
  status: IssueStatusModel.fromJson(json['status'] as Map<String, dynamic>),
  priority: IssuePriorityModel.fromJson(
    json['priority'] as Map<String, dynamic>,
  ),
  subject: json['subject'] as String,
  description: json['description'] as String? ?? '',
  category: (json['category'] as num?)?.toInt(),
  fixedVersion: json['fixedVersion'] == null
      ? null
      : IssueVersionModel.fromJson(
          json['fixedVersion'] as Map<String, dynamic>,
        ),
  assignedTo: json['assignedTo'] == null
      ? null
      : SimpleUserModel.fromJson(json['assignedTo'] as Map<String, dynamic>),
  parent: json['parent'] == null
      ? null
      : ParentIssueModel.fromJson(json['parent'] as Map<String, dynamic>),
  watchers:
      (json['watchers'] as List<dynamic>?)
          ?.map((e) => SimpleUserModel.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  isPrivate: json['isPrivate'] as bool? ?? false,
  expectedDuration: json['expectedDuration'] as String?,
  expectedDurationDisplay: json['expectedDurationDisplay'] as String? ?? '',
  startDate: json['startDate'] as String,
  dueDate: json['dueDate'] as String?,
  meeting: (json['meeting'] as num?)?.toInt(),
  meetingDesc: json['meetingDesc'] == null
      ? null
      : MeetingDescModel.fromJson(json['meetingDesc'] as Map<String, dynamic>),
  doneRatio: (json['doneRatio'] as num?)?.toInt() ?? 0,
  closed: json['closed'] as String?,
  files:
      (json['files'] as List<dynamic>?)
          ?.map((e) => IssueFileModel.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  links:
      (json['links'] as List<dynamic>?)
          ?.map((e) => IssueLinkModel.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  subIssues:
      (json['subIssues'] as List<dynamic>?)
          ?.map((e) => SubIssueModel.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  outgoingRelations:
      (json['outgoingRelations'] as List<dynamic>?)
          ?.map((e) => IssueRelationModel.fromJson(e as Map<String, dynamic>))
          .toList() ??
      const [],
  incomingRelation: json['incomingRelation'] == null
      ? null
      : IssueRelationModel.fromJson(
          json['incomingRelation'] as Map<String, dynamic>,
        ),
  creator: json['creator'] == null
      ? null
      : SimpleUserModel.fromJson(json['creator'] as Map<String, dynamic>),
  updater: (json['updater'] as num?)?.toInt(),
  created: json['created'] as String,
  updated: json['updated'] as String,
);

Map<String, dynamic> _$$IssueModelImplToJson(_$IssueModelImpl instance) =>
    <String, dynamic>{
      'pk': instance.pk,
      'project': instance.project,
      'tracker': instance.tracker,
      'status': instance.status,
      'priority': instance.priority,
      'subject': instance.subject,
      'description': instance.description,
      'category': instance.category,
      'fixedVersion': instance.fixedVersion,
      'assignedTo': instance.assignedTo,
      'parent': instance.parent,
      'watchers': instance.watchers,
      'isPrivate': instance.isPrivate,
      'expectedDuration': instance.expectedDuration,
      'expectedDurationDisplay': instance.expectedDurationDisplay,
      'startDate': instance.startDate,
      'dueDate': instance.dueDate,
      'meeting': instance.meeting,
      'meetingDesc': instance.meetingDesc,
      'doneRatio': instance.doneRatio,
      'closed': instance.closed,
      'files': instance.files,
      'links': instance.links,
      'subIssues': instance.subIssues,
      'outgoingRelations': instance.outgoingRelations,
      'incomingRelation': instance.incomingRelation,
      'creator': instance.creator,
      'updater': instance.updater,
      'created': instance.created,
      'updated': instance.updated,
    };

_$IssueListResponseImpl _$$IssueListResponseImplFromJson(
  Map<String, dynamic> json,
) => _$IssueListResponseImpl(
  count: (json['count'] as num).toInt(),
  next: json['next'] as String?,
  previous: json['previous'] as String?,
  results: (json['results'] as List<dynamic>)
      .map((e) => IssueModel.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$$IssueListResponseImplToJson(
  _$IssueListResponseImpl instance,
) => <String, dynamic>{
  'count': instance.count,
  'next': instance.next,
  'previous': instance.previous,
  'results': instance.results,
};
