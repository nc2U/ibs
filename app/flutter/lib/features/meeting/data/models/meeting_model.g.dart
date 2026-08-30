// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'meeting_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$MeetingCategoryModelImpl _$$MeetingCategoryModelImplFromJson(
  Map<String, dynamic> json,
) => _$MeetingCategoryModelImpl(
  pk: (json['pk'] as num).toInt(),
  name: json['name'] as String,
  color: json['color'] as String? ?? '#6366F1',
  order: (json['order'] as num?)?.toInt() ?? 0,
);

Map<String, dynamic> _$$MeetingCategoryModelImplToJson(
  _$MeetingCategoryModelImpl instance,
) => <String, dynamic>{
  'pk': instance.pk,
  'name': instance.name,
  'color': instance.color,
  'order': instance.order,
};

_$MeetingFileModelImpl _$$MeetingFileModelImplFromJson(
  Map<String, dynamic> json,
) => _$MeetingFileModelImpl(
  pk: (json['pk'] as num).toInt(),
  file: json['file'] as String,
  fileName: json['file_name'] as String,
  fileType: json['file_type'] as String? ?? '',
  fileSize: (json['file_size'] as num?)?.toInt(),
  description: json['description'] as String? ?? '',
  created: json['created'] as String,
  creator: json['creator'] == null
      ? null
      : SimpleUserModel.fromJson(json['creator'] as Map<String, dynamic>),
);

Map<String, dynamic> _$$MeetingFileModelImplToJson(
  _$MeetingFileModelImpl instance,
) => <String, dynamic>{
  'pk': instance.pk,
  'file': instance.file,
  'file_name': instance.fileName,
  'file_type': instance.fileType,
  'file_size': instance.fileSize,
  'description': instance.description,
  'created': instance.created,
  'creator': instance.creator,
};

_$MeetingLinkModelImpl _$$MeetingLinkModelImplFromJson(
  Map<String, dynamic> json,
) => _$MeetingLinkModelImpl(
  pk: (json['pk'] as num).toInt(),
  link: json['link'] as String,
  name: json['name'] as String,
  hit: (json['hit'] as num?)?.toInt() ?? 0,
  created: json['created'] as String,
  creator: json['creator'] == null
      ? null
      : SimpleUserModel.fromJson(json['creator'] as Map<String, dynamic>),
);

Map<String, dynamic> _$$MeetingLinkModelImplToJson(
  _$MeetingLinkModelImpl instance,
) => <String, dynamic>{
  'pk': instance.pk,
  'link': instance.link,
  'name': instance.name,
  'hit': instance.hit,
  'created': instance.created,
  'creator': instance.creator,
};

_$IssueInMeetingModelImpl _$$IssueInMeetingModelImplFromJson(
  Map<String, dynamic> json,
) => _$IssueInMeetingModelImpl(
  pk: (json['pk'] as num).toInt(),
  project: json['project'] as String,
  subject: json['subject'] as String,
  status: json['status'] as String,
  assignedTo: json['assigned_to'] == null
      ? null
      : SimpleUserModel.fromJson(json['assigned_to'] as Map<String, dynamic>),
  closed: json['closed'] as String?,
);

Map<String, dynamic> _$$IssueInMeetingModelImplToJson(
  _$IssueInMeetingModelImpl instance,
) => <String, dynamic>{
  'pk': instance.pk,
  'project': instance.project,
  'subject': instance.subject,
  'status': instance.status,
  'assigned_to': instance.assignedTo,
  'closed': instance.closed,
};

_$MeetingModelImpl _$$MeetingModelImplFromJson(Map<String, dynamic> json) =>
    _$MeetingModelImpl(
      pk: (json['pk'] as num).toInt(),
      project: (json['project'] as num).toInt(),
      projectDesc: SimpleProjectModel.fromJson(
        json['project_desc'] as Map<String, dynamic>,
      ),
      title: json['title'] as String,
      category: (json['category'] as num?)?.toInt(),
      categoryDesc: json['category_desc'] == null
          ? null
          : MeetingCategoryModel.fromJson(
              json['category_desc'] as Map<String, dynamic>,
            ),
      status: json['status'] as String? ?? '1',
      statusDisplay: json['status_display'] as String? ?? '예정',
      isConfirmed: json['is_confirmed'] as bool? ?? false,
      agenda: json['agenda'] as String? ?? '',
      content: json['content'] as String? ?? '',
      decisions: json['decisions'] as String? ?? '',
      actionItems: json['action_items'] as String? ?? '',
      meetingDate: json['meeting_date'] as String,
      location: json['location'] as String? ?? '',
      attendees:
          (json['attendees'] as List<dynamic>?)
              ?.map((e) => (e as num).toInt())
              .toList() ??
          const [],
      attendeesDesc:
          (json['attendees_desc'] as List<dynamic>?)
              ?.map((e) => SimpleUserModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      otherAttendees: json['other_attendees'] as String? ?? '',
      files:
          (json['files'] as List<dynamic>?)
              ?.map((e) => MeetingFileModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      links:
          (json['links'] as List<dynamic>?)
              ?.map((e) => MeetingLinkModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      issues:
          (json['issues'] as List<dynamic>?)
              ?.map(
                (e) => IssueInMeetingModel.fromJson(e as Map<String, dynamic>),
              )
              .toList() ??
          const [],
      creator: json['creator'] == null
          ? null
          : SimpleUserModel.fromJson(json['creator'] as Map<String, dynamic>),
      updater: json['updater'] == null
          ? null
          : SimpleUserModel.fromJson(json['updater'] as Map<String, dynamic>),
      created: json['created'] as String,
      updated: json['updated'] as String,
    );

Map<String, dynamic> _$$MeetingModelImplToJson(_$MeetingModelImpl instance) =>
    <String, dynamic>{
      'pk': instance.pk,
      'project': instance.project,
      'project_desc': instance.projectDesc,
      'title': instance.title,
      'category': instance.category,
      'category_desc': instance.categoryDesc,
      'status': instance.status,
      'status_display': instance.statusDisplay,
      'is_confirmed': instance.isConfirmed,
      'agenda': instance.agenda,
      'content': instance.content,
      'decisions': instance.decisions,
      'action_items': instance.actionItems,
      'meeting_date': instance.meetingDate,
      'location': instance.location,
      'attendees': instance.attendees,
      'attendees_desc': instance.attendeesDesc,
      'other_attendees': instance.otherAttendees,
      'files': instance.files,
      'links': instance.links,
      'issues': instance.issues,
      'creator': instance.creator,
      'updater': instance.updater,
      'created': instance.created,
      'updated': instance.updated,
    };

_$MeetingListResponseImpl _$$MeetingListResponseImplFromJson(
  Map<String, dynamic> json,
) => _$MeetingListResponseImpl(
  count: (json['count'] as num).toInt(),
  next: json['next'] as String?,
  previous: json['previous'] as String?,
  results: (json['results'] as List<dynamic>)
      .map((e) => MeetingModel.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$$MeetingListResponseImplToJson(
  _$MeetingListResponseImpl instance,
) => <String, dynamic>{
  'count': instance.count,
  'next': instance.next,
  'previous': instance.previous,
  'results': instance.results,
};
