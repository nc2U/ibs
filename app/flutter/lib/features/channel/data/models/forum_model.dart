import '../../../../core/models/common_models.dart';

/// 게시판 (Forum) 모델
class ForumModel {
  final int pk;
  final int? project;
  final String name;
  final String description;
  final int? parent;
  final bool searchAble;
  final List<int> manager;
  final int postCount;
  final int allPostCount;
  final Map<String, dynamic>? lastPost;

  const ForumModel({
    required this.pk,
    this.project,
    required this.name,
    this.description = '',
    this.parent,
    this.searchAble = true,
    this.manager = const [],
    this.postCount = 0,
    this.allPostCount = 0,
    this.lastPost,
  });

  factory ForumModel.fromJson(Map<String, dynamic> json) {
    List<int> managers = const [];
    if (json['manager'] is List) {
      managers = (json['manager'] as List)
          .map((e) => e is int ? e : int.tryParse(e.toString()))
          .whereType<int>()
          .toList();
    } else if (json['manager'] is int) {
      managers = [json['manager'] as int];
    }

    return ForumModel(
      pk: json['pk'] as int,
      project: json['project'] as int?,
      name: json['name'] as String? ?? '',
      description: json['description'] as String? ?? '',
      parent: json['parent'] as int?,
      searchAble: json['search_able'] as bool? ?? true,
      manager: managers,
      postCount: json['post_count'] as int? ?? 0,
      allPostCount: json['all_post_count'] as int? ?? 0,
      lastPost: json['last_post'] as Map<String, dynamic>?,
    );
  }
}

/// 게시글 카테고리 (PostCategory) 모델
class PostCategoryModel {
  final int pk;
  final int? forum;
  final String? color;
  final String name;
  final int? parent;
  final int order;
  final bool isManagerOnly;

  const PostCategoryModel({
    required this.pk,
    this.forum,
    this.color,
    required this.name,
    this.parent,
    this.order = 0,
    this.isManagerOnly = false,
  });

  factory PostCategoryModel.fromJson(Map<String, dynamic> json) {
    return PostCategoryModel(
      pk: json['pk'] as int,
      forum: json['forum'] as int?,
      color: json['color'] as String?,
      name: json['name'] as String? ?? '',
      parent: json['parent'] as int?,
      order: json['order'] as int? ?? 0,
      isManagerOnly: json['is_manager_only'] as bool? ?? false,
    );
  }
}

/// 게시글 첨부파일 (PostFile) 모델
class PostFileModel {
  final int pk;
  final int? post;
  final String file;
  final String fileName;
  final int? fileSize;
  final String fileType;
  final int hit;

  const PostFileModel({
    required this.pk,
    this.post,
    required this.file,
    required this.fileName,
    this.fileSize,
    this.fileType = '',
    this.hit = 0,
  });

  factory PostFileModel.fromJson(Map<String, dynamic> json) {
    return PostFileModel(
      pk: json['pk'] as int,
      post: json['post'] as int?,
      file: json['file'] as String? ?? '',
      fileName: json['file_name'] as String? ?? '',
      fileSize: json['file_size'] as int?,
      fileType: json['file_type'] as String? ?? '',
      hit: json['hit'] as int? ?? 0,
    );
  }
}

/// 게시글 댓글 (PostComment) 모델
class PostCommentModel {
  final int pk;
  final int? post;
  final String content;
  final int? parent;
  final List<PostCommentModel> replies;
  final int like;
  final bool myLike;
  final int blame;
  final bool myBlame;
  final SimpleUserModel? creator;
  final String? created;

  const PostCommentModel({
    required this.pk,
    this.post,
    required this.content,
    this.parent,
    this.replies = const [],
    this.like = 0,
    this.myLike = false,
    this.blame = 0,
    this.myBlame = false,
    this.creator,
    this.created,
  });

  factory PostCommentModel.fromJson(Map<String, dynamic> json) {
    var rawReplies = json['replies'] as List<dynamic>? ?? [];
    List<PostCommentModel> repliesList = rawReplies
        .whereType<Map<String, dynamic>>()
        .map((r) => PostCommentModel.fromJson(r))
        .toList();

    return PostCommentModel(
      pk: json['pk'] as int,
      post: json['post'] is int
          ? json['post'] as int
          : (json['post'] is Map ? (json['post']['pk'] as int?) : null),
      content: json['content'] as String? ?? '',
      parent: json['parent'] as int?,
      replies: repliesList,
      like: json['like'] as int? ?? 0,
      myLike: json['my_like'] as bool? ?? false,
      blame: json['blame'] as int? ?? 0,
      myBlame: json['my_blame'] as bool? ?? false,
      creator: json['creator'] != null
          ? SimpleUserModel.fromJson(json['creator'] as Map<String, dynamic>)
          : null,
      created: json['created'] as String?,
    );
  }
}

/// 게시글 (Post) 모델
class PostModel {
  final int pk;
  final int? forum;
  final String forumName;
  final int? category;
  final String? cateName;
  final String title;
  final String content;
  final int hit;
  final int like;
  final bool myLike;
  final int scrape;
  final bool myScrape;
  final int blame;
  final bool myBlame;
  final bool isSecret;
  final bool isHideComment;
  final bool isNotice;
  final bool isBlind;
  final List<PostFileModel> files;
  final List<PostCommentModel> comments;
  final SimpleUserModel? creator;
  final String? created;
  final String? updated;
  final bool isNew;
  final int? prevPk;
  final int? nextPk;

  const PostModel({
    required this.pk,
    this.forum,
    this.forumName = '',
    this.category,
    this.cateName,
    required this.title,
    this.content = '',
    this.hit = 0,
    this.like = 0,
    this.myLike = false,
    this.scrape = 0,
    this.myScrape = false,
    this.blame = 0,
    this.myBlame = false,
    this.isSecret = false,
    this.isHideComment = false,
    this.isNotice = false,
    this.isBlind = false,
    this.files = const [],
    this.comments = const [],
    this.creator,
    this.created,
    this.updated,
    this.isNew = false,
    this.prevPk,
    this.nextPk,
  });

  factory PostModel.fromJson(Map<String, dynamic> json) {
    var rawFiles = json['files'] as List<dynamic>? ?? [];
    List<PostFileModel> filesList = rawFiles
        .whereType<Map<String, dynamic>>()
        .map((f) => PostFileModel.fromJson(f))
        .toList();

    var rawComments = json['comments'] as List<dynamic>? ?? [];
    List<PostCommentModel> commentsList = rawComments
        .whereType<Map<String, dynamic>>()
        .map((c) => PostCommentModel.fromJson(c))
        .toList();

    return PostModel(
      pk: json['pk'] as int,
      forum: json['forum'] as int?,
      forumName: json['forum_name'] as String? ?? '',
      category: json['category'] as int?,
      cateName: json['cate_name'] as String?,
      title: json['title'] as String? ?? '',
      content: json['content'] as String? ?? '',
      hit: json['hit'] as int? ?? 0,
      like: json['like'] as int? ?? 0,
      myLike: json['my_like'] as bool? ?? false,
      scrape: json['scrape'] as int? ?? 0,
      myScrape: json['my_scrape'] as bool? ?? false,
      blame: json['blame'] as int? ?? 0,
      myBlame: json['my_blame'] as bool? ?? false,
      isSecret: json['is_secret'] as bool? ?? false,
      isHideComment: json['is_hide_comment'] as bool? ?? false,
      isNotice: json['is_notice'] as bool? ?? false,
      isBlind: json['is_blind'] as bool? ?? false,
      files: filesList,
      comments: commentsList,
      creator: json['creator'] != null
          ? SimpleUserModel.fromJson(json['creator'] as Map<String, dynamic>)
          : null,
      created: json['created'] as String?,
      updated: json['updated'] as String?,
      isNew: json['is_new'] as bool? ?? false,
      prevPk: json['prev_pk'] as int?,
      nextPk: json['next_pk'] as int?,
    );
  }
}

/// 게시글 목록 응답 (Pagination)
class PostListResponse {
  final int count;
  final String? next;
  final String? previous;
  final List<PostModel> results;

  const PostListResponse({
    required this.count,
    this.next,
    this.previous,
    required this.results,
  });

  factory PostListResponse.fromJson(Map<String, dynamic> json) {
    final rawResults = json['results'] as List<dynamic>? ?? [];
    return PostListResponse(
      count: json['count'] as int? ?? 0,
      next: json['next'] as String?,
      previous: json['previous'] as String?,
      results: rawResults
          .map((e) => PostModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}
