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
      pk: json['pk'] as int? ?? 0,
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
  final SearchUserInfo? creator;
  final bool isPrivate;

  const IssueSearchResult({
    required this.pk,
    required this.project,
    required this.subject,
    required this.created,
    required this.trackerName,
    required this.statusName,
    this.creator,
    this.isPrivate = false,
  });

  factory IssueSearchResult.fromJson(Map<String, dynamic> json) {
    final projJson = json['project'] as Map<String, dynamic>? ?? {};
    final trackerJson = json['tracker'] as Map<String, dynamic>? ?? {};
    final statusJson = json['status'] as Map<String, dynamic>? ?? {};
    final creatorJson = json['creator'] as Map<String, dynamic>?;

    return IssueSearchResult(
      pk: json['pk'] as int? ?? 0,
      project: SearchProjectInfo.fromJson(projJson),
      subject: json['subject']?.toString() ?? '',
      created: json['created']?.toString() ?? '',
      trackerName: trackerJson['name']?.toString() ?? '',
      statusName: statusJson['name']?.toString() ?? '',
      creator: creatorJson != null ? SearchUserInfo.fromJson(creatorJson) : null,
      isPrivate: json['is_private'] as bool? ?? false,
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

  factory MeetingSearchResult.fromJson(Map<String, dynamic> json) {
    final projJson = json['project'] as Map<String, dynamic>? ?? {};
    final creatorJson = json['creator'] as Map<String, dynamic>?;

    return MeetingSearchResult(
      pk: json['pk'] as int? ?? 0,
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
    final projJson = json['project'] as Map<String, dynamic>? ?? {};
    final creatorJson = json['creator'] as Map<String, dynamic>?;

    return DocumentSearchResult(
      pk: json['pk'] as int? ?? 0,
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
    final projJson = json['project'] as Map<String, dynamic>? ?? {};
    final authorJson = json['author'] as Map<String, dynamic>?;

    return NewsSearchResult(
      pk: json['pk'] as int? ?? 0,
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
    final projJson = json['project'] as Map<String, dynamic>? ?? {};
    final creatorJson = json['creator'] as Map<String, dynamic>?;

    return PostSearchResult(
      pk: json['pk'] as int? ?? 0,
      project: SearchProjectInfo.fromJson(projJson),
      forum: json['forum'] as int? ?? 0,
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
    final issueJson = json['issue'] as Map<String, dynamic>? ?? {};
    final projJson = issueJson['project'] as Map<String, dynamic>? ?? {};
    final creatorJson = json['creator'] as Map<String, dynamic>?;

    return CommentSearchResult(
      pk: json['pk'] as int? ?? 0,
      issuePk: issueJson['pk'] as int? ?? 0,
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
    return UnifiedSearchResponse(
      issues: (json['issues'] as List<dynamic>?)
              ?.map((e) => IssueSearchResult.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      meetings: (json['meetings'] as List<dynamic>?)
              ?.map((e) => MeetingSearchResult.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      documents: (json['documents'] as List<dynamic>?)
              ?.map((e) => DocumentSearchResult.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      news: (json['news'] as List<dynamic>?)
              ?.map((e) => NewsSearchResult.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      posts: (json['posts'] as List<dynamic>?)
              ?.map((e) => PostSearchResult.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      comments: (json['comments'] as List<dynamic>?)
              ?.map((e) => CommentSearchResult.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}
