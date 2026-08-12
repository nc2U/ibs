// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'common_models.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
  'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models',
);

SimpleUserModel _$SimpleUserModelFromJson(Map<String, dynamic> json) {
  return _SimpleUserModel.fromJson(json);
}

/// @nodoc
mixin _$SimpleUserModel {
  int get pk => throw _privateConstructorUsedError;
  String get username => throw _privateConstructorUsedError;
  String? get email => throw _privateConstructorUsedError;

  /// Serializes this SimpleUserModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of SimpleUserModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $SimpleUserModelCopyWith<SimpleUserModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $SimpleUserModelCopyWith<$Res> {
  factory $SimpleUserModelCopyWith(
    SimpleUserModel value,
    $Res Function(SimpleUserModel) then,
  ) = _$SimpleUserModelCopyWithImpl<$Res, SimpleUserModel>;
  @useResult
  $Res call({int pk, String username, String? email});
}

/// @nodoc
class _$SimpleUserModelCopyWithImpl<$Res, $Val extends SimpleUserModel>
    implements $SimpleUserModelCopyWith<$Res> {
  _$SimpleUserModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of SimpleUserModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? username = null,
    Object? email = freezed,
  }) {
    return _then(
      _value.copyWith(
            pk: null == pk
                ? _value.pk
                : pk // ignore: cast_nullable_to_non_nullable
                      as int,
            username: null == username
                ? _value.username
                : username // ignore: cast_nullable_to_non_nullable
                      as String,
            email: freezed == email
                ? _value.email
                : email // ignore: cast_nullable_to_non_nullable
                      as String?,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$SimpleUserModelImplCopyWith<$Res>
    implements $SimpleUserModelCopyWith<$Res> {
  factory _$$SimpleUserModelImplCopyWith(
    _$SimpleUserModelImpl value,
    $Res Function(_$SimpleUserModelImpl) then,
  ) = __$$SimpleUserModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({int pk, String username, String? email});
}

/// @nodoc
class __$$SimpleUserModelImplCopyWithImpl<$Res>
    extends _$SimpleUserModelCopyWithImpl<$Res, _$SimpleUserModelImpl>
    implements _$$SimpleUserModelImplCopyWith<$Res> {
  __$$SimpleUserModelImplCopyWithImpl(
    _$SimpleUserModelImpl _value,
    $Res Function(_$SimpleUserModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of SimpleUserModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? username = null,
    Object? email = freezed,
  }) {
    return _then(
      _$SimpleUserModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        username: null == username
            ? _value.username
            : username // ignore: cast_nullable_to_non_nullable
                  as String,
        email: freezed == email
            ? _value.email
            : email // ignore: cast_nullable_to_non_nullable
                  as String?,
      ),
    );
  }
}

/// @nodoc
@JsonSerializable()
class _$SimpleUserModelImpl implements _SimpleUserModel {
  const _$SimpleUserModelImpl({
    required this.pk,
    required this.username,
    this.email,
  });

  factory _$SimpleUserModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$SimpleUserModelImplFromJson(json);

  @override
  final int pk;
  @override
  final String username;
  @override
  final String? email;

  @override
  String toString() {
    return 'SimpleUserModel(pk: $pk, username: $username, email: $email)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SimpleUserModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.username, username) ||
                other.username == username) &&
            (identical(other.email, email) || other.email == email));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, pk, username, email);

  /// Create a copy of SimpleUserModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$SimpleUserModelImplCopyWith<_$SimpleUserModelImpl> get copyWith =>
      __$$SimpleUserModelImplCopyWithImpl<_$SimpleUserModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$SimpleUserModelImplToJson(this);
  }
}

abstract class _SimpleUserModel implements SimpleUserModel {
  const factory _SimpleUserModel({
    required final int pk,
    required final String username,
    final String? email,
  }) = _$SimpleUserModelImpl;

  factory _SimpleUserModel.fromJson(Map<String, dynamic> json) =
      _$SimpleUserModelImpl.fromJson;

  @override
  int get pk;
  @override
  String get username;
  @override
  String? get email;

  /// Create a copy of SimpleUserModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$SimpleUserModelImplCopyWith<_$SimpleUserModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

SimpleProjectModel _$SimpleProjectModelFromJson(Map<String, dynamic> json) {
  return _SimpleProjectModel.fromJson(json);
}

/// @nodoc
mixin _$SimpleProjectModel {
  int get pk => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  String get slug => throw _privateConstructorUsedError;

  /// Serializes this SimpleProjectModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of SimpleProjectModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $SimpleProjectModelCopyWith<SimpleProjectModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $SimpleProjectModelCopyWith<$Res> {
  factory $SimpleProjectModelCopyWith(
    SimpleProjectModel value,
    $Res Function(SimpleProjectModel) then,
  ) = _$SimpleProjectModelCopyWithImpl<$Res, SimpleProjectModel>;
  @useResult
  $Res call({int pk, String name, String slug});
}

/// @nodoc
class _$SimpleProjectModelCopyWithImpl<$Res, $Val extends SimpleProjectModel>
    implements $SimpleProjectModelCopyWith<$Res> {
  _$SimpleProjectModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of SimpleProjectModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({Object? pk = null, Object? name = null, Object? slug = null}) {
    return _then(
      _value.copyWith(
            pk: null == pk
                ? _value.pk
                : pk // ignore: cast_nullable_to_non_nullable
                      as int,
            name: null == name
                ? _value.name
                : name // ignore: cast_nullable_to_non_nullable
                      as String,
            slug: null == slug
                ? _value.slug
                : slug // ignore: cast_nullable_to_non_nullable
                      as String,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$SimpleProjectModelImplCopyWith<$Res>
    implements $SimpleProjectModelCopyWith<$Res> {
  factory _$$SimpleProjectModelImplCopyWith(
    _$SimpleProjectModelImpl value,
    $Res Function(_$SimpleProjectModelImpl) then,
  ) = __$$SimpleProjectModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({int pk, String name, String slug});
}

/// @nodoc
class __$$SimpleProjectModelImplCopyWithImpl<$Res>
    extends _$SimpleProjectModelCopyWithImpl<$Res, _$SimpleProjectModelImpl>
    implements _$$SimpleProjectModelImplCopyWith<$Res> {
  __$$SimpleProjectModelImplCopyWithImpl(
    _$SimpleProjectModelImpl _value,
    $Res Function(_$SimpleProjectModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of SimpleProjectModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({Object? pk = null, Object? name = null, Object? slug = null}) {
    return _then(
      _$SimpleProjectModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        name: null == name
            ? _value.name
            : name // ignore: cast_nullable_to_non_nullable
                  as String,
        slug: null == slug
            ? _value.slug
            : slug // ignore: cast_nullable_to_non_nullable
                  as String,
      ),
    );
  }
}

/// @nodoc
@JsonSerializable()
class _$SimpleProjectModelImpl implements _SimpleProjectModel {
  const _$SimpleProjectModelImpl({
    required this.pk,
    required this.name,
    required this.slug,
  });

  factory _$SimpleProjectModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$SimpleProjectModelImplFromJson(json);

  @override
  final int pk;
  @override
  final String name;
  @override
  final String slug;

  @override
  String toString() {
    return 'SimpleProjectModel(pk: $pk, name: $name, slug: $slug)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SimpleProjectModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.slug, slug) || other.slug == slug));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, pk, name, slug);

  /// Create a copy of SimpleProjectModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$SimpleProjectModelImplCopyWith<_$SimpleProjectModelImpl> get copyWith =>
      __$$SimpleProjectModelImplCopyWithImpl<_$SimpleProjectModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$SimpleProjectModelImplToJson(this);
  }
}

abstract class _SimpleProjectModel implements SimpleProjectModel {
  const factory _SimpleProjectModel({
    required final int pk,
    required final String name,
    required final String slug,
  }) = _$SimpleProjectModelImpl;

  factory _SimpleProjectModel.fromJson(Map<String, dynamic> json) =
      _$SimpleProjectModelImpl.fromJson;

  @override
  int get pk;
  @override
  String get name;
  @override
  String get slug;

  /// Create a copy of SimpleProjectModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$SimpleProjectModelImplCopyWith<_$SimpleProjectModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
