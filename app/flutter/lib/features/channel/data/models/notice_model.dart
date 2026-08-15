import '../../../../core/models/common_models.dart';

class NoticeFileModel {
  final int pk;
  final int? news;
  final String file;
  final String fileName;
  final String fileType;
  final int? fileSize;
  final String description;
  final SimpleUserModel? creator;
  final String? created;

  const NoticeFileModel({
    required this.pk,
    this.news,
    required this.file,
    required this.fileName,
    this.fileType = '',
    this.fileSize,
    this.description = '',
    this.creator,
    this.created,
  });

  factory NoticeFileModel.fromJson(Map<String, dynamic> json) {
    return NoticeFileModel(
      pk: json['pk'] as int,
      news: json['news'] as int?,
      file: json['file'] as String? ?? '',
      fileName: json['file_name'] as String? ?? '',
      fileType: json['file_type'] as String? ?? '',
      fileSize: json['file_size'] as int?,
      description: json['description'] as String? ?? '',
      creator: json['creator'] != null
          ? SimpleUserModel.fromJson(json['creator'] as Map<String, dynamic>)
          : null,
      created: json['created'] as String?,
    );
  }
}

class NoticeCommentModel {
  final int pk;
  final int? news;
  final String content;
  final int? parent;
  final SimpleUserModel? creator;
  final String? created;
  final String? updated;

  const NoticeCommentModel({
    required this.pk,
    this.news,
    required this.content,
    this.parent,
    this.creator,
    this.created,
    this.updated,
  });

  factory NoticeCommentModel.fromJson(Map<String, dynamic> json) {
    return NoticeCommentModel(
      pk: json['pk'] as int,
      news: json['news'] as int?,
      content: json['content'] as String? ?? '',
      parent: json['parent'] as int?,
      creator: json['creator'] != null
          ? SimpleUserModel.fromJson(json['creator'] as Map<String, dynamic>)
          : null,
      created: json['created'] as String?,
      updated: json['updated'] as String?,
    );
  }
}

class NoticeModel {
  final int pk;
  final SimpleProjectModel? project;
  final String title;
  final String summary;
  final String content;
  final bool isImportant;
  final SimpleUserModel? author;
  final List<NoticeFileModel> files;
  final List<NoticeCommentModel> comments;
  final bool isNew;
  final String? created;
  final String? updated;

  const NoticeModel({
    required this.pk,
    this.project,
    required this.title,
    this.summary = '',
    this.content = '',
    this.isImportant = false,
    this.author,
    this.files = const [],
    this.comments = const [],
    this.isNew = false,
    this.created,
    this.updated,
  });

  factory NoticeModel.fromJson(Map<String, dynamic> json) {
    return NoticeModel(
      pk: json['pk'] as int,
      project: json['project'] != null
          ? SimpleProjectModel.fromJson(json['project'] as Map<String, dynamic>)
          : null,
      title: json['title'] as String? ?? '',
      summary: json['summary'] as String? ?? '',
      content: json['content'] as String? ?? '',
      isImportant: json['is_important'] as bool? ?? false,
      author: json['author'] != null
          ? SimpleUserModel.fromJson(json['author'] as Map<String, dynamic>)
          : null,
      files: (json['files'] as List<dynamic>?)
              ?.map((f) => NoticeFileModel.fromJson(f as Map<String, dynamic>))
              .toList() ??
          const [],
      comments: (json['comments'] as List<dynamic>?)
              ?.map((c) => NoticeCommentModel.fromJson(c as Map<String, dynamic>))
              .toList() ??
          const [],
      isNew: json['is_new'] as bool? ?? false,
      created: json['created'] as String?,
      updated: json['updated'] as String?,
    );
  }
}

class NoticeListResponse {
  final int count;
  final String? next;
  final String? previous;
  final List<NoticeModel> results;

  const NoticeListResponse({
    required this.count,
    this.next,
    this.previous,
    required this.results,
  });

  factory NoticeListResponse.fromJson(Map<String, dynamic> json) {
    return NoticeListResponse(
      count: json['count'] as int? ?? 0,
      next: json['next'] as String?,
      previous: json['previous'] as String?,
      results: (json['results'] as List<dynamic>?)
              ?.map((e) => NoticeModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );
  }
}
