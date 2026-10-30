int _parseInt(dynamic val, [int fallback = 0]) {
  if (val == null) return fallback;
  if (val is int) return val;
  if (val is num) return val.toInt();
  if (val is String) return int.tryParse(val) ?? fallback;
  return fallback;
}

Map<String, dynamic> _asMap(dynamic val) {
  if (val is Map<String, dynamic>) return val;
  if (val is Map) return Map<String, dynamic>.from(val);
  return const {};
}

Map<String, dynamic>? _asNullableMap(dynamic val) {
  if (val is Map<String, dynamic>) return val;
  if (val is Map) return Map<String, dynamic>.from(val);
  return null;
}

class SearchProjectInfo {
  final String slug;
  final String name;

  const SearchProjectInfo({required this.slug, required this.name});

  factory SearchProjectInfo.fromJson(Map<String, dynamic> json) {
    return SearchProjectInfo(
      slug: json['slug']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
    );
  }
}

class SearchUserInfo {
  final int pk;
  final String username;

  const SearchUserInfo({required this.pk, required this.username});

  factory SearchUserInfo.fromJson(Map<String, dynamic> json) {
    return SearchUserInfo(
      pk: _parseInt(json['pk']),
      username: json['username']?.toString() ?? '',
    );
  }
}

class IssueSearchResult {
  final int pk;
  final SearchProjectInfo project;
  final String subject;
  final String created;
  final String trackerName;
  final String statusName;
  final bool statusClosed;
  final SearchUserInfo? creator;
  final bool isPrivate;

  const IssueSearchResult({
    required this.pk,
    required this.project,
    required this.subject,
    required this.created,
    required this.trackerName,
    required this.statusName,
    this.statusClosed = false,
    this.creator,
    this.isPrivate = false,
  });

  factory IssueSearchResult.fromJson(Map<String, dynamic> json) {
    final projJson = _asMap(json['project']);
    final trackerJson = _asMap(json['tracker']);
    final statusJson = _asMap(json['status']);
    final creatorJson = _asNullableMap(json['creator']);

    return IssueSearchResult(
      pk: _parseInt(json['pk']),
      project: SearchProjectInfo.fromJson(projJson),
      subject: json['subject']?.toString() ?? '',
      created: json['created']?.toString() ?? '',
      trackerName: trackerJson['name']?.toString() ?? '',
      statusName: statusJson['name']?.toString() ?? '',
      statusClosed: statusJson['closed'] == true,
      creator: creatorJson != null ? SearchUserInfo.fromJson(creatorJson) : null,
      isPrivate: json['is_private'] == true,
    );
  }
}

class MeetingSearchResult {
  final int pk;
  final SearchProjectInfo project;
  final String title;
  final String meetingDate;
  final String status;
  final SearchUserInfo? creator;

  const MeetingSearchResult({
    required this.pk,
    required this.project,
    required this.title,
    required this.meetingDate,
    required this.status,
    this.creator,
  });

  /// 백엔드 Meeting.MEETING_STATUS_CHOICES: ('1': '준비', '2': '종료', '3': '취소')
  String get statusLabel {
    switch (status) {
      case '1':
        return '회의 · 준비';
      case '2':
        return '회의 · 종료';
      case '3':
        return '회의 · 취소';
      default:
        return '회의록';
    }
  }

  factory MeetingSearchResult.fromJson(Map<String, dynamic> json) {
    final projJson = _asMap(json['project']);
    final creatorJson = _asNullableMap(json['creator']);

    return MeetingSearchResult(
      pk: _parseInt(json['pk']),
      project: SearchProjectInfo.fromJson(projJson),
      title: json['title']?.toString() ?? '',
      meetingDate: json['meeting_date']?.toString() ?? '',
      status: json['status']?.toString() ?? '1',
      creator: creatorJson != null ? SearchUserInfo.fromJson(creatorJson) : null,
    );
  }
}

class DocumentSearchResult {
  final int pk;
  final SearchProjectInfo project;
  final String title;
  final String description;
  final String created;
  final SearchUserInfo? creator;

  const DocumentSearchResult({
    required this.pk,
    required this.project,
    required this.title,
    required this.description,
    required this.created,
    this.creator,
  });

  factory DocumentSearchResult.fromJson(Map<String, dynamic> json) {
    final projJson = _asMap(json['project']);
    final creatorJson = _asNullableMap(json['creator']);

    return DocumentSearchResult(
      pk: _parseInt(json['pk']),
      project: SearchProjectInfo.fromJson(projJson),
      title: json['title']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      created: json['created']?.toString() ?? '',
      creator: creatorJson != null ? SearchUserInfo.fromJson(creatorJson) : null,
    );
  }
}

class NewsSearchResult {
  final int pk;
  final SearchProjectInfo project;
  final String title;
  final String summary;
  final String created;
  final SearchUserInfo? author;

  const NewsSearchResult({
    required this.pk,
    required this.project,
    required this.title,
    required this.summary,
    required this.created,
    this.author,
  });

  factory NewsSearchResult.fromJson(Map<String, dynamic> json) {
    final projJson = _asMap(json['project']);
    final authorJson = _asNullableMap(json['author']);

    return NewsSearchResult(
      pk: _parseInt(json['pk']),
      project: SearchProjectInfo.fromJson(projJson),
      title: json['title']?.toString() ?? '',
      summary: json['summary']?.toString() ?? '',
      created: json['created']?.toString() ?? '',
      author: authorJson != null ? SearchUserInfo.fromJson(authorJson) : null,
    );
  }
}

class PostSearchResult {
  final int pk;
  final SearchProjectInfo project;
  final int forum;
  final String title;
  final String created;
  final SearchUserInfo? creator;

  const PostSearchResult({
    required this.pk,
    required this.project,
    required this.forum,
    required this.title,
    required this.created,
    this.creator,
  });

  factory PostSearchResult.fromJson(Map<String, dynamic> json) {
    final projJson = _asMap(json['project']);
    final creatorJson = _asNullableMap(json['creator']);

    return PostSearchResult(
      pk: _parseInt(json['pk']),
      project: SearchProjectInfo.fromJson(projJson),
      forum: _parseInt(json['forum']),
      title: json['title']?.toString() ?? '',
      created: json['created']?.toString() ?? '',
      creator: creatorJson != null ? SearchUserInfo.fromJson(creatorJson) : null,
    );
  }
}

class CommentSearchResult {
  final int pk;
  final int issuePk;
  final String issueSubject;
  final SearchProjectInfo project;
  final String content;
  final String created;
  final SearchUserInfo? creator;

  const CommentSearchResult({
    required this.pk,
    required this.issuePk,
    required this.issueSubject,
    required this.project,
    required this.content,
    required this.created,
    this.creator,
  });

  factory CommentSearchResult.fromJson(Map<String, dynamic> json) {
    final issueJson = _asMap(json['issue']);
    final projJson = _asMap(issueJson['project']);
    final creatorJson = _asNullableMap(json['creator']);

    return CommentSearchResult(
      pk: _parseInt(json['pk']),
      issuePk: _parseInt(issueJson['pk']),
      issueSubject: issueJson['subject']?.toString() ?? '',
      project: SearchProjectInfo.fromJson(projJson),
      content: json['content']?.toString() ?? '',
      created: json['created']?.toString() ?? '',
      creator: creatorJson != null ? SearchUserInfo.fromJson(creatorJson) : null,
    );
  }
}

class UnifiedSearchResponse {
  final List<IssueSearchResult> issues;
  final List<MeetingSearchResult> meetings;
  final List<DocumentSearchResult> documents;
  final List<NewsSearchResult> news;
  final List<PostSearchResult> posts;
  final List<CommentSearchResult> comments;

  const UnifiedSearchResponse({
    this.issues = const [],
    this.meetings = const [],
    this.documents = const [],
    this.news = const [],
    this.posts = const [],
    this.comments = const [],
  });

  int get totalCount =>
      issues.length +
      meetings.length +
      documents.length +
      news.length +
      posts.length +
      comments.length;

  bool get isEmpty => totalCount == 0;

  factory UnifiedSearchResponse.fromJson(Map<String, dynamic> json) {
    List<T> parseList<T>(dynamic raw, T Function(Map<String, dynamic>) mapper) {
      if (raw is! List) return const [];
      return raw.whereType<Map>().map((e) => mapper(_asMap(e))).toList();
    }

    return UnifiedSearchResponse(
      issues: parseList(json['issues'], IssueSearchResult.fromJson),
      meetings: parseList(json['meetings'], MeetingSearchResult.fromJson),
      documents: parseList(json['documents'], DocumentSearchResult.fromJson),
      news: parseList(json['news'], NewsSearchResult.fromJson),
      posts: parseList(json['posts'], PostSearchResult.fromJson),
      comments: parseList(json['comments'], CommentSearchResult.fromJson),
    );
  }
}
