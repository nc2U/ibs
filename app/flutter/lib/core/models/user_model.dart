/// 프로필 모델 (실명, 연락처, 아바타 이미지 및 업무/알림 설정)
class ProfileModel {
  final int? pk;
  final String? name;
  final String? birthDate;
  final String? cellPhone;
  final String? image;
  final bool autoWatchCreated;
  final bool autoWatchAssigned;
  final bool meetingCreatedNotification;
  final bool meetingConfirmedNotification;

  const ProfileModel({
    this.pk,
    this.name,
    this.birthDate,
    this.cellPhone,
    this.image,
    this.autoWatchCreated = true,
    this.autoWatchAssigned = true,
    this.meetingCreatedNotification = true,
    this.meetingConfirmedNotification = true,
  });

  factory ProfileModel.fromJson(Map<String, dynamic> json) {
    return ProfileModel(
      pk: json['pk'] as int?,
      name: json['name'] as String?,
      birthDate: json['birth_date'] as String?,
      cellPhone: json['cell_phone'] as String?,
      image: json['image'] as String?,
      autoWatchCreated: json['auto_watch_created'] as bool? ?? true,
      autoWatchAssigned: json['auto_watch_assigned'] as bool? ?? true,
      meetingCreatedNotification: json['meeting_created_notification'] as bool? ?? true,
      meetingConfirmedNotification: json['meeting_confirmed_notification'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'pk': pk,
      'name': name,
      'birth_date': birthDate,
      'cell_phone': cellPhone,
      'image': image,
      'auto_watch_created': autoWatchCreated,
      'auto_watch_assigned': autoWatchAssigned,
      'meeting_created_notification': meetingCreatedNotification,
      'meeting_confirmed_notification': meetingConfirmedNotification,
    };
  }

  ProfileModel copyWith({
    int? pk,
    String? name,
    String? birthDate,
    String? cellPhone,
    String? image,
    bool? autoWatchCreated,
    bool? autoWatchAssigned,
    bool? meetingCreatedNotification,
    bool? meetingConfirmedNotification,
  }) {
    return ProfileModel(
      pk: pk ?? this.pk,
      name: name ?? this.name,
      birthDate: birthDate ?? this.birthDate,
      cellPhone: cellPhone ?? this.cellPhone,
      image: image ?? this.image,
      autoWatchCreated: autoWatchCreated ?? this.autoWatchCreated,
      autoWatchAssigned: autoWatchAssigned ?? this.autoWatchAssigned,
      meetingCreatedNotification: meetingCreatedNotification ?? this.meetingCreatedNotification,
      meetingConfirmedNotification: meetingConfirmedNotification ?? this.meetingConfirmedNotification,
    );
  }
}

/// 사용자 상세 모델 (로그인 사용자 정보 및 권한)
class UserModel {
  final int pk;
  final String username;
  final String? email;
  final bool isSuperuser;
  final bool isStaff;
  final bool workManager;
  final ProfileModel? profile;

  const UserModel({
    required this.pk,
    required this.username,
    this.email,
    this.isSuperuser = false,
    this.isStaff = false,
    this.workManager = false,
    this.profile,
  });

  /// 표출용 명칭 (실명이 등록되어 있으면 '실명 (아이디)' 또는 '실명')
  String get displayName {
    if (profile?.name != null && profile!.name!.trim().isNotEmpty) {
      return '${profile!.name!.trim()} ($username)';
    }
    return username;
  }

  /// 실명 또는 아이디
  String get nameOrUsername {
    if (profile?.name != null && profile!.name!.trim().isNotEmpty) {
      return profile!.name!.trim();
    }
    return username;
  }

  /// 아바타 이미지 URL
  String? get avatarUrl => profile?.image;

  /// 아바타 fallback 이니셜
  String get initial {
    final target = nameOrUsername;
    if (target.isNotEmpty) {
      return target.substring(0, 1).toUpperCase();
    }
    return 'U';
  }

  factory UserModel.fromJson(Map<String, dynamic> json) {
    ProfileModel? profileObj;
    if (json['profile'] != null && json['profile'] is Map<String, dynamic>) {
      profileObj = ProfileModel.fromJson(json['profile'] as Map<String, dynamic>);
    }

    return UserModel(
      pk: json['pk'] as int,
      username: json['username'] as String? ?? '',
      email: json['email'] as String?,
      isSuperuser: json['is_superuser'] as bool? ?? false,
      isStaff: json['is_staff'] as bool? ?? false,
      workManager: json['work_manager'] as bool? ?? false,
      profile: profileObj,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'pk': pk,
      'username': username,
      'email': email,
      'is_superuser': isSuperuser,
      'is_staff': isStaff,
      'work_manager': workManager,
      'profile': profile?.toJson(),
    };
  }
}
