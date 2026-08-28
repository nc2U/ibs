import '../../../../core/models/common_models.dart';

class ProjectMemberModel {
  final int pk;
  final SimpleUserModel user;

  const ProjectMemberModel({required this.pk, required this.user});

  factory ProjectMemberModel.fromJson(Map<String, dynamic> json) {
    return ProjectMemberModel(
      pk: json['pk'] as int? ?? 0,
      user: SimpleUserModel.fromJson(
          json['user'] as Map<String, dynamic>? ?? {}),
    );
  }
}

class ProjectVersionModel {
  final int pk;
  final String name;
  final String status;
  final bool isDefault;

  const ProjectVersionModel({
    required this.pk,
    required this.name,
    this.status = '1',
    this.isDefault = false,
  });

  factory ProjectVersionModel.fromJson(Map<String, dynamic> json) {
    return ProjectVersionModel(
      pk: json['pk'] as int? ?? 0,
      name: json['name']?.toString() ?? '',
      status: json['status']?.toString() ?? '1',
      isDefault: json['is_default'] as bool? ?? false,
    );
  }
}

class ProjectTrackerModel {
  final int pk;
  final String name;
  final String description;

  const ProjectTrackerModel({
    required this.pk,
    required this.name,
    this.description = '',
  });

  factory ProjectTrackerModel.fromJson(Map<String, dynamic> json) {
    return ProjectTrackerModel(
      pk: json['pk'] as int? ?? 0,
      name: json['name']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
    );
  }
}

class ProjectModuleModel {
  final bool issue;
  final bool meeting;
  final bool news;
  final bool document;
  final bool forum;
  final bool calendar;

  const ProjectModuleModel({
    this.issue = true,
    this.meeting = true,
    this.news = true,
    this.document = true,
    this.forum = true,
    this.calendar = true,
  });

  factory ProjectModuleModel.fromJson(Map<String, dynamic> json) {
    return ProjectModuleModel(
      issue: json['issue'] as bool? ?? true,
      meeting: json['meeting'] as bool? ?? true,
      news: json['news'] as bool? ?? true,
      document: json['document'] as bool? ?? true,
      forum: json['forum'] as bool? ?? true,
      calendar: json['calendar'] as bool? ?? true,
    );
  }
}

class ProjectCategoryModel {
  final int pk;
  final String name;
  final SimpleUserModel? assignedTo;

  const ProjectCategoryModel({
    required this.pk,
    required this.name,
    this.assignedTo,
  });

  factory ProjectCategoryModel.fromJson(Map<String, dynamic> json) {
    return ProjectCategoryModel(
      pk: json['pk'] as int? ?? 0,
      name: json['name']?.toString() ?? '',
      assignedTo: json['assigned_to'] != null
          ? SimpleUserModel.fromJson(
              json['assigned_to'] as Map<String, dynamic>)
          : null,
    );
  }
}

class ProjectModel {
  final int pk;
  final int? projectId; // 실제 부동산 개발 프로젝트(Project) PK
  final String name;
  final String slug;
  final String description;
  final String type;
  final String status;
  final bool visible;
  final bool isPublic;
  final bool isBookmarked;
  final int depth;
  final bool parentVisible;
  final int? parent;
  final List<ProjectModel> subProjects;
  final ProjectModuleModel? module;
  final List<String> myPerms;
  final List<ProjectMemberModel> members;
  final List<ProjectVersionModel> versions;
  final List<ProjectCategoryModel> categories;
  final List<ProjectTrackerModel> trackers;

  const ProjectModel({
    required this.pk,
    this.projectId,
    this.name = '',
    this.slug = '',
    this.description = '',
    this.type = '1',
    this.status = '1',
    this.visible = true,
    this.isPublic = false,
    this.isBookmarked = false,
    this.depth = 0,
    this.parentVisible = false,
    this.parent,
    this.subProjects = const [],
    this.module,
    this.myPerms = const [],
    this.members = const [],
    this.versions = const [],
    this.categories = const [],
    this.trackers = const [],
  });

  /// 계층형 들여쓰기가 적용된 표시 라벨 (Vue와 100% 동일)
  String get indentedLabel {
    if (depth > 0 && parentVisible) {
      return '${'  ' * depth}» $name';
    }
    return name;
  }

  ProjectModel copyWith({
    int? pk,
    int? projectId,
    String? name,
    String? slug,
    String? description,
    String? type,
    String? status,
    bool? visible,
    bool? isPublic,
    bool? isBookmarked,
    int? depth,
    bool? parentVisible,
    int? parent,
    List<ProjectModel>? subProjects,
    ProjectModuleModel? module,
    List<String>? myPerms,
    List<ProjectMemberModel>? members,
    List<ProjectVersionModel>? versions,
    List<ProjectCategoryModel>? categories,
    List<ProjectTrackerModel>? trackers,
  }) {
    return ProjectModel(
      pk: pk ?? this.pk,
      projectId: projectId ?? this.projectId,
      name: name ?? this.name,
      slug: slug ?? this.slug,
      description: description ?? this.description,
      type: type ?? this.type,
      status: status ?? this.status,
      visible: visible ?? this.visible,
      isPublic: isPublic ?? this.isPublic,
      isBookmarked: isBookmarked ?? this.isBookmarked,
      depth: depth ?? this.depth,
      parentVisible: parentVisible ?? this.parentVisible,
      parent: parent ?? this.parent,
      subProjects: subProjects ?? List.from(this.subProjects),
      module: module ?? this.module,
      myPerms: myPerms ?? this.myPerms,
      members: members ?? this.members,
      versions: versions ?? this.versions,
      categories: categories ?? this.categories,
      trackers: trackers ?? this.trackers,
    );
  }

  factory ProjectModel.fromJson(Map<String, dynamic> json) {
    final memberList = (json['all_members'] ?? json['members']) as List<dynamic>?;
    return ProjectModel(
      pk: json['pk'] as int? ?? 0,
      projectId: json['project'] as int?,
      name: json['name']?.toString() ?? '',
      slug: json['slug']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      type: json['type']?.toString() ?? '1',
      status: json['status']?.toString() ?? '1',
      visible: json['visible'] as bool? ?? true,
      isPublic: json['is_public'] as bool? ?? false,
      isBookmarked: json['is_bookmarked'] as bool? ?? false,
      depth: json['depth'] as int? ?? 0,
      parentVisible: json['parent_visible'] as bool? ?? false,
      parent: json['parent'] as int?,
      subProjects: const [],
      module: json['module'] != null
          ? ProjectModuleModel.fromJson(json['module'] as Map<String, dynamic>)
          : null,
      myPerms: (json['my_perms'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      members: (memberList != null)
          ? memberList
              .whereType<Map<String, dynamic>>()
              .map((e) => ProjectMemberModel.fromJson(e))
              .toList()
          : <ProjectMemberModel>[],
      versions: (json['versions'] is List)
          ? (json['versions'] as List)
              .whereType<Map<String, dynamic>>()
              .map((e) => ProjectVersionModel.fromJson(e))
              .toList()
          : <ProjectVersionModel>[],
      categories: (json['categories'] is List)
          ? (json['categories'] as List)
              .whereType<Map<String, dynamic>>()
              .map((e) => ProjectCategoryModel.fromJson(e))
              .toList()
          : <ProjectCategoryModel>[],
      trackers: (json['trackers'] is List)
          ? (json['trackers'] as List)
              .whereType<Map<String, dynamic>>()
              .map((e) => ProjectTrackerModel.fromJson(e))
              .toList()
          : <ProjectTrackerModel>[],
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
        'parent': parent,
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

/// 🏢 부동산 개발 프로젝트(Project) 상세 개요 및 기본 설정 모델 (/api/v1/project/{id}/)
class RealEstateProjectDetailModel {
  final int pk;
  final int? company;
  final int? issueProject;
  final String? issueProjectSlug;
  final String name;
  final int order;
  final String kind;
  final String? kindDesc;
  final int startYear;
  final bool isDirectManage;
  final bool isReturnedArea;
  final bool isUnitSet;
  final String monthlyAggrStartDate;
  final String constructionStartDate;
  final int constructionPeriodMonths;
  final String location;
  final String areaUsage;
  final String buildSize;
  final int? numUnit;
  final double? buyLandExtent;
  final double? schemeLandExtent;
  final double? donationLandExtent;
  final double? onFloorArea;
  final double? underFloorArea;
  final double? totalFloorArea;
  final double? buildArea;
  final double? floorAreaRatio;
  final double? buildToLandRatio;
  final int? numLegalParking;
  final int? numPlanedParking;

  const RealEstateProjectDetailModel({
    required this.pk,
    this.company,
    this.issueProject,
    this.issueProjectSlug,
    required this.name,
    this.order = 100,
    required this.kind,
    this.kindDesc,
    required this.startYear,
    this.isDirectManage = false,
    this.isReturnedArea = false,
    this.isUnitSet = false,
    required this.monthlyAggrStartDate,
    required this.constructionStartDate,
    required this.constructionPeriodMonths,
    this.location = '',
    this.areaUsage = '',
    this.buildSize = '',
    this.numUnit,
    this.buyLandExtent,
    this.schemeLandExtent,
    this.donationLandExtent,
    this.onFloorArea,
    this.underFloorArea,
    this.totalFloorArea,
    this.buildArea,
    this.floorAreaRatio,
    this.buildToLandRatio,
    this.numLegalParking,
    this.numPlanedParking,
  });

  factory RealEstateProjectDetailModel.fromJson(Map<String, dynamic> json) {
    double? parseDouble(dynamic v) {
      if (v == null) return null;
      if (v is num) return v.toDouble();
      return double.tryParse(v.toString());
    }

    int? parseInt(dynamic v) {
      if (v == null) return null;
      if (v is int) return v;
      return int.tryParse(v.toString());
    }

    return RealEstateProjectDetailModel(
      pk: json['pk'] as int? ?? json['id'] as int? ?? 0,
      company: json['company'] as int?,
      issueProject: json['issue_project'] as int?,
      issueProjectSlug: json['issue_project_slug']?.toString(),
      name: json['name']?.toString() ?? '',
      order: json['order'] as int? ?? 100,
      kind: json['kind']?.toString() ?? '1',
      kindDesc: json['kind_desc']?.toString(),
      startYear: json['start_year'] as int? ?? DateTime.now().year,
      isDirectManage: json['is_direct_manage'] as bool? ?? false,
      isReturnedArea: json['is_returned_area'] as bool? ?? false,
      isUnitSet: json['is_unit_set'] as bool? ?? false,
      monthlyAggrStartDate: json['monthly_aggr_start_date']?.toString() ?? '',
      constructionStartDate: json['construction_start_date']?.toString() ?? '',
      constructionPeriodMonths: json['construction_period_months'] as int? ?? 0,
      location: json['location']?.toString() ?? '',
      areaUsage: json['area_usage']?.toString() ?? '',
      buildSize: json['build_size']?.toString() ?? '',
      numUnit: parseInt(json['num_unit']),
      buyLandExtent: parseDouble(json['buy_land_extent']),
      schemeLandExtent: parseDouble(json['scheme_land_extent']),
      donationLandExtent: parseDouble(json['donation_land_extent']),
      onFloorArea: parseDouble(json['on_floor_area']),
      underFloorArea: parseDouble(json['under_floor_area']),
      totalFloorArea: parseDouble(json['total_floor_area']),
      buildArea: parseDouble(json['build_area']),
      floorAreaRatio: parseDouble(json['floor_area_ratio']),
      buildToLandRatio: parseDouble(json['build_to_land_ratio']),
      numLegalParking: parseInt(json['num_legal_parking']),
      numPlanedParking: parseInt(json['num_planed_parking']),
    );
  }
}
