import 'package:flutter/foundation.dart';

int _readPk(Map<String, dynamic> json) {
  final val = json['pk'] ?? json['id'];
  if (val is num) return val.toInt();
  if (val is String) return int.tryParse(val) ?? 0;
  return 0;
}

@immutable
class SimpleUserModel {
  final int pk;
  final String username;
  final String name;
  final String? email;
  final String? fullName;

  const SimpleUserModel({
    required this.pk,
    this.username = '',
    this.name = '',
    this.email,
    this.fullName,
  });

  factory SimpleUserModel.fromJson(Map<String, dynamic> json) {
    return SimpleUserModel(
      pk: _readPk(json),
      username: json['username'] as String? ?? '',
      name: json['name'] as String? ?? '',
      email: json['email'] as String?,
      fullName: json['full_name'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'pk': pk,
      'username': username,
      'name': name,
      if (email != null) 'email': email,
      if (fullName != null) 'full_name': fullName,
    };
  }

  SimpleUserModel copyWith({
    int? pk,
    String? username,
    String? name,
    String? email,
    String? fullName,
  }) {
    return SimpleUserModel(
      pk: pk ?? this.pk,
      username: username ?? this.username,
      name: name ?? this.name,
      email: email ?? this.email,
      fullName: fullName ?? this.fullName,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is SimpleUserModel &&
          runtimeType == other.runtimeType &&
          pk == other.pk &&
          username == other.username &&
          name == other.name &&
          email == other.email &&
          fullName == other.fullName;

  @override
  int get hashCode =>
      pk.hashCode ^
      username.hashCode ^
      name.hashCode ^
      (email?.hashCode ?? 0) ^
      (fullName?.hashCode ?? 0);
}

extension SimpleUserModelX on SimpleUserModel {
  String get displayName => name.isNotEmpty ? '$name ($username)' : username;
}

@immutable
class SimpleProjectModel {
  final int pk;
  final String name;
  final String slug;

  const SimpleProjectModel({
    required this.pk,
    this.name = '',
    this.slug = '',
  });

  factory SimpleProjectModel.fromJson(Map<String, dynamic> json) {
    return SimpleProjectModel(
      pk: _readPk(json),
      name: json['name'] as String? ?? '',
      slug: json['slug'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'pk': pk,
      'name': name,
      'slug': slug,
    };
  }

  SimpleProjectModel copyWith({
    int? pk,
    String? name,
    String? slug,
  }) {
    return SimpleProjectModel(
      pk: pk ?? this.pk,
      name: name ?? this.name,
      slug: slug ?? this.slug,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is SimpleProjectModel &&
          runtimeType == other.runtimeType &&
          pk == other.pk &&
          name == other.name &&
          slug == other.slug;

  @override
  int get hashCode => pk.hashCode ^ name.hashCode ^ slug.hashCode;
}
