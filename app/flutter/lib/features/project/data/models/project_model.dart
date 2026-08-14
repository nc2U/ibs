class ProjectModel {
  final int pk;
  final String name;
  final String slug;
  final String description;
  final String type;
  final String status;
  final bool visible;
  final bool isPublic;
  final bool isBookmarked;
  final List<String> myPerms;

  const ProjectModel({
    required this.pk,
    this.name = '',
    this.slug = '',
    this.description = '',
    this.type = '1',
    this.status = '1',
    this.visible = true,
    this.isPublic = false,
    this.isBookmarked = false,
    this.myPerms = const [],
  });

  factory ProjectModel.fromJson(Map<String, dynamic> json) {
    return ProjectModel(
      pk: json['pk'] as int? ?? 0,
      name: json['name']?.toString() ?? '',
      slug: json['slug']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      type: json['type']?.toString() ?? '1',
      status: json['status']?.toString() ?? '1',
      visible: json['visible'] as bool? ?? true,
      isPublic: json['is_public'] as bool? ?? false,
      isBookmarked: json['is_bookmarked'] as bool? ?? false,
      myPerms: (json['my_perms'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
    );
  }

  Map<String, dynamic> toJson() => {
        'pk': pk,
        'name': name,
        'slug': slug,
        'description': description,
        'type': type,
        'status': status,
        'visible': visible,
        'is_public': isPublic,
        'is_bookmarked': isBookmarked,
        'my_perms': myPerms,
      };
}

class ProjectListResponse {
  final int count;
  final String? next;
  final String? previous;
  final List<ProjectModel> results;

  const ProjectListResponse({
    required this.count,
    this.next,
    this.previous,
    required this.results,
  });

  factory ProjectListResponse.fromJson(Map<String, dynamic> json) {
    return ProjectListResponse(
      count: json['count'] as int? ?? 0,
      next: json['next'] as String?,
      previous: json['previous'] as String?,
      results: (json['results'] as List<dynamic>?)
              ?.map((e) => ProjectModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );
  }
}
