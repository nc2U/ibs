// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'issue_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
  'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models',
);

IssueStatusModel _$IssueStatusModelFromJson(Map<String, dynamic> json) {
  return _IssueStatusModel.fromJson(json);
}

/// @nodoc
mixin _$IssueStatusModel {
  int get pk => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  bool get closed => throw _privateConstructorUsedError;

  /// Serializes this IssueStatusModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of IssueStatusModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $IssueStatusModelCopyWith<IssueStatusModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $IssueStatusModelCopyWith<$Res> {
  factory $IssueStatusModelCopyWith(
    IssueStatusModel value,
    $Res Function(IssueStatusModel) then,
  ) = _$IssueStatusModelCopyWithImpl<$Res, IssueStatusModel>;
  @useResult
  $Res call({int pk, String name, bool closed});
}

/// @nodoc
class _$IssueStatusModelCopyWithImpl<$Res, $Val extends IssueStatusModel>
    implements $IssueStatusModelCopyWith<$Res> {
  _$IssueStatusModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of IssueStatusModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({Object? pk = null, Object? name = null, Object? closed = null}) {
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
            closed: null == closed
                ? _value.closed
                : closed // ignore: cast_nullable_to_non_nullable
                      as bool,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$IssueStatusModelImplCopyWith<$Res>
    implements $IssueStatusModelCopyWith<$Res> {
  factory _$$IssueStatusModelImplCopyWith(
    _$IssueStatusModelImpl value,
    $Res Function(_$IssueStatusModelImpl) then,
  ) = __$$IssueStatusModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({int pk, String name, bool closed});
}

/// @nodoc
class __$$IssueStatusModelImplCopyWithImpl<$Res>
    extends _$IssueStatusModelCopyWithImpl<$Res, _$IssueStatusModelImpl>
    implements _$$IssueStatusModelImplCopyWith<$Res> {
  __$$IssueStatusModelImplCopyWithImpl(
    _$IssueStatusModelImpl _value,
    $Res Function(_$IssueStatusModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of IssueStatusModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({Object? pk = null, Object? name = null, Object? closed = null}) {
    return _then(
      _$IssueStatusModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        name: null == name
            ? _value.name
            : name // ignore: cast_nullable_to_non_nullable
                  as String,
        closed: null == closed
            ? _value.closed
            : closed // ignore: cast_nullable_to_non_nullable
                  as bool,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$IssueStatusModelImpl implements _IssueStatusModel {
  const _$IssueStatusModelImpl({
    required this.pk,
    required this.name,
    required this.closed,
  });

  factory _$IssueStatusModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$IssueStatusModelImplFromJson(json);

  @override
  final int pk;
  @override
  final String name;
  @override
  final bool closed;

  @override
  String toString() {
    return 'IssueStatusModel(pk: $pk, name: $name, closed: $closed)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$IssueStatusModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.closed, closed) || other.closed == closed));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, pk, name, closed);

  /// Create a copy of IssueStatusModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$IssueStatusModelImplCopyWith<_$IssueStatusModelImpl> get copyWith =>
      __$$IssueStatusModelImplCopyWithImpl<_$IssueStatusModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$IssueStatusModelImplToJson(this);
  }
}

abstract class _IssueStatusModel implements IssueStatusModel {
  const factory _IssueStatusModel({
    required final int pk,
    required final String name,
    required final bool closed,
  }) = _$IssueStatusModelImpl;

  factory _IssueStatusModel.fromJson(Map<String, dynamic> json) =
      _$IssueStatusModelImpl.fromJson;

  @override
  int get pk;
  @override
  String get name;
  @override
  bool get closed;

  /// Create a copy of IssueStatusModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$IssueStatusModelImplCopyWith<_$IssueStatusModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

IssuePriorityModel _$IssuePriorityModelFromJson(Map<String, dynamic> json) {
  return _IssuePriorityModel.fromJson(json);
}

/// @nodoc
mixin _$IssuePriorityModel {
  int get pk => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;

  /// Serializes this IssuePriorityModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of IssuePriorityModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $IssuePriorityModelCopyWith<IssuePriorityModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $IssuePriorityModelCopyWith<$Res> {
  factory $IssuePriorityModelCopyWith(
    IssuePriorityModel value,
    $Res Function(IssuePriorityModel) then,
  ) = _$IssuePriorityModelCopyWithImpl<$Res, IssuePriorityModel>;
  @useResult
  $Res call({int pk, String name});
}

/// @nodoc
class _$IssuePriorityModelCopyWithImpl<$Res, $Val extends IssuePriorityModel>
    implements $IssuePriorityModelCopyWith<$Res> {
  _$IssuePriorityModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of IssuePriorityModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({Object? pk = null, Object? name = null}) {
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
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$IssuePriorityModelImplCopyWith<$Res>
    implements $IssuePriorityModelCopyWith<$Res> {
  factory _$$IssuePriorityModelImplCopyWith(
    _$IssuePriorityModelImpl value,
    $Res Function(_$IssuePriorityModelImpl) then,
  ) = __$$IssuePriorityModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({int pk, String name});
}

/// @nodoc
class __$$IssuePriorityModelImplCopyWithImpl<$Res>
    extends _$IssuePriorityModelCopyWithImpl<$Res, _$IssuePriorityModelImpl>
    implements _$$IssuePriorityModelImplCopyWith<$Res> {
  __$$IssuePriorityModelImplCopyWithImpl(
    _$IssuePriorityModelImpl _value,
    $Res Function(_$IssuePriorityModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of IssuePriorityModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({Object? pk = null, Object? name = null}) {
    return _then(
      _$IssuePriorityModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        name: null == name
            ? _value.name
            : name // ignore: cast_nullable_to_non_nullable
                  as String,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$IssuePriorityModelImpl implements _IssuePriorityModel {
  const _$IssuePriorityModelImpl({required this.pk, required this.name});

  factory _$IssuePriorityModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$IssuePriorityModelImplFromJson(json);

  @override
  final int pk;
  @override
  final String name;

  @override
  String toString() {
    return 'IssuePriorityModel(pk: $pk, name: $name)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$IssuePriorityModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.name, name) || other.name == name));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, pk, name);

  /// Create a copy of IssuePriorityModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$IssuePriorityModelImplCopyWith<_$IssuePriorityModelImpl> get copyWith =>
      __$$IssuePriorityModelImplCopyWithImpl<_$IssuePriorityModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$IssuePriorityModelImplToJson(this);
  }
}

abstract class _IssuePriorityModel implements IssuePriorityModel {
  const factory _IssuePriorityModel({
    required final int pk,
    required final String name,
  }) = _$IssuePriorityModelImpl;

  factory _IssuePriorityModel.fromJson(Map<String, dynamic> json) =
      _$IssuePriorityModelImpl.fromJson;

  @override
  int get pk;
  @override
  String get name;

  /// Create a copy of IssuePriorityModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$IssuePriorityModelImplCopyWith<_$IssuePriorityModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

IssueTrackerModel _$IssueTrackerModelFromJson(Map<String, dynamic> json) {
  return _IssueTrackerModel.fromJson(json);
}

/// @nodoc
mixin _$IssueTrackerModel {
  int get pk => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;

  /// Serializes this IssueTrackerModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of IssueTrackerModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $IssueTrackerModelCopyWith<IssueTrackerModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $IssueTrackerModelCopyWith<$Res> {
  factory $IssueTrackerModelCopyWith(
    IssueTrackerModel value,
    $Res Function(IssueTrackerModel) then,
  ) = _$IssueTrackerModelCopyWithImpl<$Res, IssueTrackerModel>;
  @useResult
  $Res call({int pk, String name, String description});
}

/// @nodoc
class _$IssueTrackerModelCopyWithImpl<$Res, $Val extends IssueTrackerModel>
    implements $IssueTrackerModelCopyWith<$Res> {
  _$IssueTrackerModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of IssueTrackerModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? name = null,
    Object? description = null,
  }) {
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
            description: null == description
                ? _value.description
                : description // ignore: cast_nullable_to_non_nullable
                      as String,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$IssueTrackerModelImplCopyWith<$Res>
    implements $IssueTrackerModelCopyWith<$Res> {
  factory _$$IssueTrackerModelImplCopyWith(
    _$IssueTrackerModelImpl value,
    $Res Function(_$IssueTrackerModelImpl) then,
  ) = __$$IssueTrackerModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({int pk, String name, String description});
}

/// @nodoc
class __$$IssueTrackerModelImplCopyWithImpl<$Res>
    extends _$IssueTrackerModelCopyWithImpl<$Res, _$IssueTrackerModelImpl>
    implements _$$IssueTrackerModelImplCopyWith<$Res> {
  __$$IssueTrackerModelImplCopyWithImpl(
    _$IssueTrackerModelImpl _value,
    $Res Function(_$IssueTrackerModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of IssueTrackerModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? name = null,
    Object? description = null,
  }) {
    return _then(
      _$IssueTrackerModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        name: null == name
            ? _value.name
            : name // ignore: cast_nullable_to_non_nullable
                  as String,
        description: null == description
            ? _value.description
            : description // ignore: cast_nullable_to_non_nullable
                  as String,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$IssueTrackerModelImpl implements _IssueTrackerModel {
  const _$IssueTrackerModelImpl({
    required this.pk,
    required this.name,
    this.description = '',
  });

  factory _$IssueTrackerModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$IssueTrackerModelImplFromJson(json);

  @override
  final int pk;
  @override
  final String name;
  @override
  @JsonKey()
  final String description;

  @override
  String toString() {
    return 'IssueTrackerModel(pk: $pk, name: $name, description: $description)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$IssueTrackerModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.description, description) ||
                other.description == description));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, pk, name, description);

  /// Create a copy of IssueTrackerModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$IssueTrackerModelImplCopyWith<_$IssueTrackerModelImpl> get copyWith =>
      __$$IssueTrackerModelImplCopyWithImpl<_$IssueTrackerModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$IssueTrackerModelImplToJson(this);
  }
}

abstract class _IssueTrackerModel implements IssueTrackerModel {
  const factory _IssueTrackerModel({
    required final int pk,
    required final String name,
    final String description,
  }) = _$IssueTrackerModelImpl;

  factory _IssueTrackerModel.fromJson(Map<String, dynamic> json) =
      _$IssueTrackerModelImpl.fromJson;

  @override
  int get pk;
  @override
  String get name;
  @override
  String get description;

  /// Create a copy of IssueTrackerModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$IssueTrackerModelImplCopyWith<_$IssueTrackerModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

IssueVersionModel _$IssueVersionModelFromJson(Map<String, dynamic> json) {
  return _IssueVersionModel.fromJson(json);
}

/// @nodoc
mixin _$IssueVersionModel {
  int get pk => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;

  /// Serializes this IssueVersionModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of IssueVersionModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $IssueVersionModelCopyWith<IssueVersionModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $IssueVersionModelCopyWith<$Res> {
  factory $IssueVersionModelCopyWith(
    IssueVersionModel value,
    $Res Function(IssueVersionModel) then,
  ) = _$IssueVersionModelCopyWithImpl<$Res, IssueVersionModel>;
  @useResult
  $Res call({int pk, String name, String description});
}

/// @nodoc
class _$IssueVersionModelCopyWithImpl<$Res, $Val extends IssueVersionModel>
    implements $IssueVersionModelCopyWith<$Res> {
  _$IssueVersionModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of IssueVersionModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? name = null,
    Object? description = null,
  }) {
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
            description: null == description
                ? _value.description
                : description // ignore: cast_nullable_to_non_nullable
                      as String,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$IssueVersionModelImplCopyWith<$Res>
    implements $IssueVersionModelCopyWith<$Res> {
  factory _$$IssueVersionModelImplCopyWith(
    _$IssueVersionModelImpl value,
    $Res Function(_$IssueVersionModelImpl) then,
  ) = __$$IssueVersionModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({int pk, String name, String description});
}

/// @nodoc
class __$$IssueVersionModelImplCopyWithImpl<$Res>
    extends _$IssueVersionModelCopyWithImpl<$Res, _$IssueVersionModelImpl>
    implements _$$IssueVersionModelImplCopyWith<$Res> {
  __$$IssueVersionModelImplCopyWithImpl(
    _$IssueVersionModelImpl _value,
    $Res Function(_$IssueVersionModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of IssueVersionModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? name = null,
    Object? description = null,
  }) {
    return _then(
      _$IssueVersionModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        name: null == name
            ? _value.name
            : name // ignore: cast_nullable_to_non_nullable
                  as String,
        description: null == description
            ? _value.description
            : description // ignore: cast_nullable_to_non_nullable
                  as String,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$IssueVersionModelImpl implements _IssueVersionModel {
  const _$IssueVersionModelImpl({
    required this.pk,
    required this.name,
    this.description = '',
  });

  factory _$IssueVersionModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$IssueVersionModelImplFromJson(json);

  @override
  final int pk;
  @override
  final String name;
  @override
  @JsonKey()
  final String description;

  @override
  String toString() {
    return 'IssueVersionModel(pk: $pk, name: $name, description: $description)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$IssueVersionModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.description, description) ||
                other.description == description));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, pk, name, description);

  /// Create a copy of IssueVersionModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$IssueVersionModelImplCopyWith<_$IssueVersionModelImpl> get copyWith =>
      __$$IssueVersionModelImplCopyWithImpl<_$IssueVersionModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$IssueVersionModelImplToJson(this);
  }
}

abstract class _IssueVersionModel implements IssueVersionModel {
  const factory _IssueVersionModel({
    required final int pk,
    required final String name,
    final String description,
  }) = _$IssueVersionModelImpl;

  factory _IssueVersionModel.fromJson(Map<String, dynamic> json) =
      _$IssueVersionModelImpl.fromJson;

  @override
  int get pk;
  @override
  String get name;
  @override
  String get description;

  /// Create a copy of IssueVersionModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$IssueVersionModelImplCopyWith<_$IssueVersionModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

MeetingDescModel _$MeetingDescModelFromJson(Map<String, dynamic> json) {
  return _MeetingDescModel.fromJson(json);
}

/// @nodoc
mixin _$MeetingDescModel {
  int get pk => throw _privateConstructorUsedError;
  String get title => throw _privateConstructorUsedError;

  /// Serializes this MeetingDescModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of MeetingDescModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $MeetingDescModelCopyWith<MeetingDescModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MeetingDescModelCopyWith<$Res> {
  factory $MeetingDescModelCopyWith(
    MeetingDescModel value,
    $Res Function(MeetingDescModel) then,
  ) = _$MeetingDescModelCopyWithImpl<$Res, MeetingDescModel>;
  @useResult
  $Res call({int pk, String title});
}

/// @nodoc
class _$MeetingDescModelCopyWithImpl<$Res, $Val extends MeetingDescModel>
    implements $MeetingDescModelCopyWith<$Res> {
  _$MeetingDescModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of MeetingDescModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({Object? pk = null, Object? title = null}) {
    return _then(
      _value.copyWith(
            pk: null == pk
                ? _value.pk
                : pk // ignore: cast_nullable_to_non_nullable
                      as int,
            title: null == title
                ? _value.title
                : title // ignore: cast_nullable_to_non_nullable
                      as String,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$MeetingDescModelImplCopyWith<$Res>
    implements $MeetingDescModelCopyWith<$Res> {
  factory _$$MeetingDescModelImplCopyWith(
    _$MeetingDescModelImpl value,
    $Res Function(_$MeetingDescModelImpl) then,
  ) = __$$MeetingDescModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({int pk, String title});
}

/// @nodoc
class __$$MeetingDescModelImplCopyWithImpl<$Res>
    extends _$MeetingDescModelCopyWithImpl<$Res, _$MeetingDescModelImpl>
    implements _$$MeetingDescModelImplCopyWith<$Res> {
  __$$MeetingDescModelImplCopyWithImpl(
    _$MeetingDescModelImpl _value,
    $Res Function(_$MeetingDescModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of MeetingDescModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({Object? pk = null, Object? title = null}) {
    return _then(
      _$MeetingDescModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        title: null == title
            ? _value.title
            : title // ignore: cast_nullable_to_non_nullable
                  as String,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$MeetingDescModelImpl implements _MeetingDescModel {
  const _$MeetingDescModelImpl({required this.pk, required this.title});

  factory _$MeetingDescModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$MeetingDescModelImplFromJson(json);

  @override
  final int pk;
  @override
  final String title;

  @override
  String toString() {
    return 'MeetingDescModel(pk: $pk, title: $title)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MeetingDescModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.title, title) || other.title == title));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, pk, title);

  /// Create a copy of MeetingDescModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$MeetingDescModelImplCopyWith<_$MeetingDescModelImpl> get copyWith =>
      __$$MeetingDescModelImplCopyWithImpl<_$MeetingDescModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$MeetingDescModelImplToJson(this);
  }
}

abstract class _MeetingDescModel implements MeetingDescModel {
  const factory _MeetingDescModel({
    required final int pk,
    required final String title,
  }) = _$MeetingDescModelImpl;

  factory _MeetingDescModel.fromJson(Map<String, dynamic> json) =
      _$MeetingDescModelImpl.fromJson;

  @override
  int get pk;
  @override
  String get title;

  /// Create a copy of MeetingDescModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$MeetingDescModelImplCopyWith<_$MeetingDescModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ParentIssueModel _$ParentIssueModelFromJson(Map<String, dynamic> json) {
  return _ParentIssueModel.fromJson(json);
}

/// @nodoc
mixin _$ParentIssueModel {
  int get pk => throw _privateConstructorUsedError;
  String get tracker => throw _privateConstructorUsedError;
  String get subject => throw _privateConstructorUsedError;
  bool get isPrivate => throw _privateConstructorUsedError;

  /// Serializes this ParentIssueModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ParentIssueModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ParentIssueModelCopyWith<ParentIssueModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ParentIssueModelCopyWith<$Res> {
  factory $ParentIssueModelCopyWith(
    ParentIssueModel value,
    $Res Function(ParentIssueModel) then,
  ) = _$ParentIssueModelCopyWithImpl<$Res, ParentIssueModel>;
  @useResult
  $Res call({int pk, String tracker, String subject, bool isPrivate});
}

/// @nodoc
class _$ParentIssueModelCopyWithImpl<$Res, $Val extends ParentIssueModel>
    implements $ParentIssueModelCopyWith<$Res> {
  _$ParentIssueModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ParentIssueModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? tracker = null,
    Object? subject = null,
    Object? isPrivate = null,
  }) {
    return _then(
      _value.copyWith(
            pk: null == pk
                ? _value.pk
                : pk // ignore: cast_nullable_to_non_nullable
                      as int,
            tracker: null == tracker
                ? _value.tracker
                : tracker // ignore: cast_nullable_to_non_nullable
                      as String,
            subject: null == subject
                ? _value.subject
                : subject // ignore: cast_nullable_to_non_nullable
                      as String,
            isPrivate: null == isPrivate
                ? _value.isPrivate
                : isPrivate // ignore: cast_nullable_to_non_nullable
                      as bool,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$ParentIssueModelImplCopyWith<$Res>
    implements $ParentIssueModelCopyWith<$Res> {
  factory _$$ParentIssueModelImplCopyWith(
    _$ParentIssueModelImpl value,
    $Res Function(_$ParentIssueModelImpl) then,
  ) = __$$ParentIssueModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({int pk, String tracker, String subject, bool isPrivate});
}

/// @nodoc
class __$$ParentIssueModelImplCopyWithImpl<$Res>
    extends _$ParentIssueModelCopyWithImpl<$Res, _$ParentIssueModelImpl>
    implements _$$ParentIssueModelImplCopyWith<$Res> {
  __$$ParentIssueModelImplCopyWithImpl(
    _$ParentIssueModelImpl _value,
    $Res Function(_$ParentIssueModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of ParentIssueModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? tracker = null,
    Object? subject = null,
    Object? isPrivate = null,
  }) {
    return _then(
      _$ParentIssueModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        tracker: null == tracker
            ? _value.tracker
            : tracker // ignore: cast_nullable_to_non_nullable
                  as String,
        subject: null == subject
            ? _value.subject
            : subject // ignore: cast_nullable_to_non_nullable
                  as String,
        isPrivate: null == isPrivate
            ? _value.isPrivate
            : isPrivate // ignore: cast_nullable_to_non_nullable
                  as bool,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$ParentIssueModelImpl implements _ParentIssueModel {
  const _$ParentIssueModelImpl({
    required this.pk,
    required this.tracker,
    required this.subject,
    this.isPrivate = false,
  });

  factory _$ParentIssueModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$ParentIssueModelImplFromJson(json);

  @override
  final int pk;
  @override
  final String tracker;
  @override
  final String subject;
  @override
  @JsonKey()
  final bool isPrivate;

  @override
  String toString() {
    return 'ParentIssueModel(pk: $pk, tracker: $tracker, subject: $subject, isPrivate: $isPrivate)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ParentIssueModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.tracker, tracker) || other.tracker == tracker) &&
            (identical(other.subject, subject) || other.subject == subject) &&
            (identical(other.isPrivate, isPrivate) ||
                other.isPrivate == isPrivate));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, pk, tracker, subject, isPrivate);

  /// Create a copy of ParentIssueModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ParentIssueModelImplCopyWith<_$ParentIssueModelImpl> get copyWith =>
      __$$ParentIssueModelImplCopyWithImpl<_$ParentIssueModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$ParentIssueModelImplToJson(this);
  }
}

abstract class _ParentIssueModel implements ParentIssueModel {
  const factory _ParentIssueModel({
    required final int pk,
    required final String tracker,
    required final String subject,
    final bool isPrivate,
  }) = _$ParentIssueModelImpl;

  factory _ParentIssueModel.fromJson(Map<String, dynamic> json) =
      _$ParentIssueModelImpl.fromJson;

  @override
  int get pk;
  @override
  String get tracker;
  @override
  String get subject;
  @override
  bool get isPrivate;

  /// Create a copy of ParentIssueModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ParentIssueModelImplCopyWith<_$ParentIssueModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

IssueFileModel _$IssueFileModelFromJson(Map<String, dynamic> json) {
  return _IssueFileModel.fromJson(json);
}

/// @nodoc
mixin _$IssueFileModel {
  int get pk => throw _privateConstructorUsedError;
  String get file => throw _privateConstructorUsedError;
  String get fileName => throw _privateConstructorUsedError;
  String get fileType => throw _privateConstructorUsedError;
  int? get fileSize => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  String get created => throw _privateConstructorUsedError;
  SimpleUserModel? get creator => throw _privateConstructorUsedError;

  /// Serializes this IssueFileModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of IssueFileModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $IssueFileModelCopyWith<IssueFileModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $IssueFileModelCopyWith<$Res> {
  factory $IssueFileModelCopyWith(
    IssueFileModel value,
    $Res Function(IssueFileModel) then,
  ) = _$IssueFileModelCopyWithImpl<$Res, IssueFileModel>;
  @useResult
  $Res call({
    int pk,
    String file,
    String fileName,
    String fileType,
    int? fileSize,
    String description,
    String created,
    SimpleUserModel? creator,
  });

  $SimpleUserModelCopyWith<$Res>? get creator;
}

/// @nodoc
class _$IssueFileModelCopyWithImpl<$Res, $Val extends IssueFileModel>
    implements $IssueFileModelCopyWith<$Res> {
  _$IssueFileModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of IssueFileModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? file = null,
    Object? fileName = null,
    Object? fileType = null,
    Object? fileSize = freezed,
    Object? description = null,
    Object? created = null,
    Object? creator = freezed,
  }) {
    return _then(
      _value.copyWith(
            pk: null == pk
                ? _value.pk
                : pk // ignore: cast_nullable_to_non_nullable
                      as int,
            file: null == file
                ? _value.file
                : file // ignore: cast_nullable_to_non_nullable
                      as String,
            fileName: null == fileName
                ? _value.fileName
                : fileName // ignore: cast_nullable_to_non_nullable
                      as String,
            fileType: null == fileType
                ? _value.fileType
                : fileType // ignore: cast_nullable_to_non_nullable
                      as String,
            fileSize: freezed == fileSize
                ? _value.fileSize
                : fileSize // ignore: cast_nullable_to_non_nullable
                      as int?,
            description: null == description
                ? _value.description
                : description // ignore: cast_nullable_to_non_nullable
                      as String,
            created: null == created
                ? _value.created
                : created // ignore: cast_nullable_to_non_nullable
                      as String,
            creator: freezed == creator
                ? _value.creator
                : creator // ignore: cast_nullable_to_non_nullable
                      as SimpleUserModel?,
          )
          as $Val,
    );
  }

  /// Create a copy of IssueFileModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SimpleUserModelCopyWith<$Res>? get creator {
    if (_value.creator == null) {
      return null;
    }

    return $SimpleUserModelCopyWith<$Res>(_value.creator!, (value) {
      return _then(_value.copyWith(creator: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$IssueFileModelImplCopyWith<$Res>
    implements $IssueFileModelCopyWith<$Res> {
  factory _$$IssueFileModelImplCopyWith(
    _$IssueFileModelImpl value,
    $Res Function(_$IssueFileModelImpl) then,
  ) = __$$IssueFileModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int pk,
    String file,
    String fileName,
    String fileType,
    int? fileSize,
    String description,
    String created,
    SimpleUserModel? creator,
  });

  @override
  $SimpleUserModelCopyWith<$Res>? get creator;
}

/// @nodoc
class __$$IssueFileModelImplCopyWithImpl<$Res>
    extends _$IssueFileModelCopyWithImpl<$Res, _$IssueFileModelImpl>
    implements _$$IssueFileModelImplCopyWith<$Res> {
  __$$IssueFileModelImplCopyWithImpl(
    _$IssueFileModelImpl _value,
    $Res Function(_$IssueFileModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of IssueFileModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? file = null,
    Object? fileName = null,
    Object? fileType = null,
    Object? fileSize = freezed,
    Object? description = null,
    Object? created = null,
    Object? creator = freezed,
  }) {
    return _then(
      _$IssueFileModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        file: null == file
            ? _value.file
            : file // ignore: cast_nullable_to_non_nullable
                  as String,
        fileName: null == fileName
            ? _value.fileName
            : fileName // ignore: cast_nullable_to_non_nullable
                  as String,
        fileType: null == fileType
            ? _value.fileType
            : fileType // ignore: cast_nullable_to_non_nullable
                  as String,
        fileSize: freezed == fileSize
            ? _value.fileSize
            : fileSize // ignore: cast_nullable_to_non_nullable
                  as int?,
        description: null == description
            ? _value.description
            : description // ignore: cast_nullable_to_non_nullable
                  as String,
        created: null == created
            ? _value.created
            : created // ignore: cast_nullable_to_non_nullable
                  as String,
        creator: freezed == creator
            ? _value.creator
            : creator // ignore: cast_nullable_to_non_nullable
                  as SimpleUserModel?,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$IssueFileModelImpl implements _IssueFileModel {
  const _$IssueFileModelImpl({
    required this.pk,
    required this.file,
    required this.fileName,
    this.fileType = '',
    this.fileSize,
    this.description = '',
    required this.created,
    this.creator,
  });

  factory _$IssueFileModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$IssueFileModelImplFromJson(json);

  @override
  final int pk;
  @override
  final String file;
  @override
  final String fileName;
  @override
  @JsonKey()
  final String fileType;
  @override
  final int? fileSize;
  @override
  @JsonKey()
  final String description;
  @override
  final String created;
  @override
  final SimpleUserModel? creator;

  @override
  String toString() {
    return 'IssueFileModel(pk: $pk, file: $file, fileName: $fileName, fileType: $fileType, fileSize: $fileSize, description: $description, created: $created, creator: $creator)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$IssueFileModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.file, file) || other.file == file) &&
            (identical(other.fileName, fileName) ||
                other.fileName == fileName) &&
            (identical(other.fileType, fileType) ||
                other.fileType == fileType) &&
            (identical(other.fileSize, fileSize) ||
                other.fileSize == fileSize) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.created, created) || other.created == created) &&
            (identical(other.creator, creator) || other.creator == creator));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
    runtimeType,
    pk,
    file,
    fileName,
    fileType,
    fileSize,
    description,
    created,
    creator,
  );

  /// Create a copy of IssueFileModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$IssueFileModelImplCopyWith<_$IssueFileModelImpl> get copyWith =>
      __$$IssueFileModelImplCopyWithImpl<_$IssueFileModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$IssueFileModelImplToJson(this);
  }
}

abstract class _IssueFileModel implements IssueFileModel {
  const factory _IssueFileModel({
    required final int pk,
    required final String file,
    required final String fileName,
    final String fileType,
    final int? fileSize,
    final String description,
    required final String created,
    final SimpleUserModel? creator,
  }) = _$IssueFileModelImpl;

  factory _IssueFileModel.fromJson(Map<String, dynamic> json) =
      _$IssueFileModelImpl.fromJson;

  @override
  int get pk;
  @override
  String get file;
  @override
  String get fileName;
  @override
  String get fileType;
  @override
  int? get fileSize;
  @override
  String get description;
  @override
  String get created;
  @override
  SimpleUserModel? get creator;

  /// Create a copy of IssueFileModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$IssueFileModelImplCopyWith<_$IssueFileModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

IssueLinkModel _$IssueLinkModelFromJson(Map<String, dynamic> json) {
  return _IssueLinkModel.fromJson(json);
}

/// @nodoc
mixin _$IssueLinkModel {
  int get pk => throw _privateConstructorUsedError;
  String get link => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  int get hit => throw _privateConstructorUsedError;
  String get created => throw _privateConstructorUsedError;
  SimpleUserModel? get creator => throw _privateConstructorUsedError;

  /// Serializes this IssueLinkModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of IssueLinkModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $IssueLinkModelCopyWith<IssueLinkModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $IssueLinkModelCopyWith<$Res> {
  factory $IssueLinkModelCopyWith(
    IssueLinkModel value,
    $Res Function(IssueLinkModel) then,
  ) = _$IssueLinkModelCopyWithImpl<$Res, IssueLinkModel>;
  @useResult
  $Res call({
    int pk,
    String link,
    String name,
    int hit,
    String created,
    SimpleUserModel? creator,
  });

  $SimpleUserModelCopyWith<$Res>? get creator;
}

/// @nodoc
class _$IssueLinkModelCopyWithImpl<$Res, $Val extends IssueLinkModel>
    implements $IssueLinkModelCopyWith<$Res> {
  _$IssueLinkModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of IssueLinkModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? link = null,
    Object? name = null,
    Object? hit = null,
    Object? created = null,
    Object? creator = freezed,
  }) {
    return _then(
      _value.copyWith(
            pk: null == pk
                ? _value.pk
                : pk // ignore: cast_nullable_to_non_nullable
                      as int,
            link: null == link
                ? _value.link
                : link // ignore: cast_nullable_to_non_nullable
                      as String,
            name: null == name
                ? _value.name
                : name // ignore: cast_nullable_to_non_nullable
                      as String,
            hit: null == hit
                ? _value.hit
                : hit // ignore: cast_nullable_to_non_nullable
                      as int,
            created: null == created
                ? _value.created
                : created // ignore: cast_nullable_to_non_nullable
                      as String,
            creator: freezed == creator
                ? _value.creator
                : creator // ignore: cast_nullable_to_non_nullable
                      as SimpleUserModel?,
          )
          as $Val,
    );
  }

  /// Create a copy of IssueLinkModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SimpleUserModelCopyWith<$Res>? get creator {
    if (_value.creator == null) {
      return null;
    }

    return $SimpleUserModelCopyWith<$Res>(_value.creator!, (value) {
      return _then(_value.copyWith(creator: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$IssueLinkModelImplCopyWith<$Res>
    implements $IssueLinkModelCopyWith<$Res> {
  factory _$$IssueLinkModelImplCopyWith(
    _$IssueLinkModelImpl value,
    $Res Function(_$IssueLinkModelImpl) then,
  ) = __$$IssueLinkModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int pk,
    String link,
    String name,
    int hit,
    String created,
    SimpleUserModel? creator,
  });

  @override
  $SimpleUserModelCopyWith<$Res>? get creator;
}

/// @nodoc
class __$$IssueLinkModelImplCopyWithImpl<$Res>
    extends _$IssueLinkModelCopyWithImpl<$Res, _$IssueLinkModelImpl>
    implements _$$IssueLinkModelImplCopyWith<$Res> {
  __$$IssueLinkModelImplCopyWithImpl(
    _$IssueLinkModelImpl _value,
    $Res Function(_$IssueLinkModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of IssueLinkModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? link = null,
    Object? name = null,
    Object? hit = null,
    Object? created = null,
    Object? creator = freezed,
  }) {
    return _then(
      _$IssueLinkModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        link: null == link
            ? _value.link
            : link // ignore: cast_nullable_to_non_nullable
                  as String,
        name: null == name
            ? _value.name
            : name // ignore: cast_nullable_to_non_nullable
                  as String,
        hit: null == hit
            ? _value.hit
            : hit // ignore: cast_nullable_to_non_nullable
                  as int,
        created: null == created
            ? _value.created
            : created // ignore: cast_nullable_to_non_nullable
                  as String,
        creator: freezed == creator
            ? _value.creator
            : creator // ignore: cast_nullable_to_non_nullable
                  as SimpleUserModel?,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$IssueLinkModelImpl implements _IssueLinkModel {
  const _$IssueLinkModelImpl({
    required this.pk,
    required this.link,
    required this.name,
    this.hit = 0,
    required this.created,
    this.creator,
  });

  factory _$IssueLinkModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$IssueLinkModelImplFromJson(json);

  @override
  final int pk;
  @override
  final String link;
  @override
  final String name;
  @override
  @JsonKey()
  final int hit;
  @override
  final String created;
  @override
  final SimpleUserModel? creator;

  @override
  String toString() {
    return 'IssueLinkModel(pk: $pk, link: $link, name: $name, hit: $hit, created: $created, creator: $creator)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$IssueLinkModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.link, link) || other.link == link) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.hit, hit) || other.hit == hit) &&
            (identical(other.created, created) || other.created == created) &&
            (identical(other.creator, creator) || other.creator == creator));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, pk, link, name, hit, created, creator);

  /// Create a copy of IssueLinkModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$IssueLinkModelImplCopyWith<_$IssueLinkModelImpl> get copyWith =>
      __$$IssueLinkModelImplCopyWithImpl<_$IssueLinkModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$IssueLinkModelImplToJson(this);
  }
}

abstract class _IssueLinkModel implements IssueLinkModel {
  const factory _IssueLinkModel({
    required final int pk,
    required final String link,
    required final String name,
    final int hit,
    required final String created,
    final SimpleUserModel? creator,
  }) = _$IssueLinkModelImpl;

  factory _IssueLinkModel.fromJson(Map<String, dynamic> json) =
      _$IssueLinkModelImpl.fromJson;

  @override
  int get pk;
  @override
  String get link;
  @override
  String get name;
  @override
  int get hit;
  @override
  String get created;
  @override
  SimpleUserModel? get creator;

  /// Create a copy of IssueLinkModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$IssueLinkModelImplCopyWith<_$IssueLinkModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

SubIssueModel _$SubIssueModelFromJson(Map<String, dynamic> json) {
  return _SubIssueModel.fromJson(json);
}

/// @nodoc
mixin _$SubIssueModel {
  int get pk => throw _privateConstructorUsedError;
  SimpleProjectModel get project => throw _privateConstructorUsedError;
  String get subject => throw _privateConstructorUsedError;
  IssueTrackerModel get tracker => throw _privateConstructorUsedError;
  String get status => throw _privateConstructorUsedError;
  SimpleUserModel? get assignedTo => throw _privateConstructorUsedError;
  List<SimpleUserModel> get watchers => throw _privateConstructorUsedError;
  int? get priority => throw _privateConstructorUsedError;
  String? get startDate => throw _privateConstructorUsedError;
  String? get dueDate => throw _privateConstructorUsedError;
  int get doneRatio => throw _privateConstructorUsedError;
  String? get closed => throw _privateConstructorUsedError;

  /// Serializes this SubIssueModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of SubIssueModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $SubIssueModelCopyWith<SubIssueModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $SubIssueModelCopyWith<$Res> {
  factory $SubIssueModelCopyWith(
    SubIssueModel value,
    $Res Function(SubIssueModel) then,
  ) = _$SubIssueModelCopyWithImpl<$Res, SubIssueModel>;
  @useResult
  $Res call({
    int pk,
    SimpleProjectModel project,
    String subject,
    IssueTrackerModel tracker,
    String status,
    SimpleUserModel? assignedTo,
    List<SimpleUserModel> watchers,
    int? priority,
    String? startDate,
    String? dueDate,
    int doneRatio,
    String? closed,
  });

  $SimpleProjectModelCopyWith<$Res> get project;
  $IssueTrackerModelCopyWith<$Res> get tracker;
  $SimpleUserModelCopyWith<$Res>? get assignedTo;
}

/// @nodoc
class _$SubIssueModelCopyWithImpl<$Res, $Val extends SubIssueModel>
    implements $SubIssueModelCopyWith<$Res> {
  _$SubIssueModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of SubIssueModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? project = null,
    Object? subject = null,
    Object? tracker = null,
    Object? status = null,
    Object? assignedTo = freezed,
    Object? watchers = null,
    Object? priority = freezed,
    Object? startDate = freezed,
    Object? dueDate = freezed,
    Object? doneRatio = null,
    Object? closed = freezed,
  }) {
    return _then(
      _value.copyWith(
            pk: null == pk
                ? _value.pk
                : pk // ignore: cast_nullable_to_non_nullable
                      as int,
            project: null == project
                ? _value.project
                : project // ignore: cast_nullable_to_non_nullable
                      as SimpleProjectModel,
            subject: null == subject
                ? _value.subject
                : subject // ignore: cast_nullable_to_non_nullable
                      as String,
            tracker: null == tracker
                ? _value.tracker
                : tracker // ignore: cast_nullable_to_non_nullable
                      as IssueTrackerModel,
            status: null == status
                ? _value.status
                : status // ignore: cast_nullable_to_non_nullable
                      as String,
            assignedTo: freezed == assignedTo
                ? _value.assignedTo
                : assignedTo // ignore: cast_nullable_to_non_nullable
                      as SimpleUserModel?,
            watchers: null == watchers
                ? _value.watchers
                : watchers // ignore: cast_nullable_to_non_nullable
                      as List<SimpleUserModel>,
            priority: freezed == priority
                ? _value.priority
                : priority // ignore: cast_nullable_to_non_nullable
                      as int?,
            startDate: freezed == startDate
                ? _value.startDate
                : startDate // ignore: cast_nullable_to_non_nullable
                      as String?,
            dueDate: freezed == dueDate
                ? _value.dueDate
                : dueDate // ignore: cast_nullable_to_non_nullable
                      as String?,
            doneRatio: null == doneRatio
                ? _value.doneRatio
                : doneRatio // ignore: cast_nullable_to_non_nullable
                      as int,
            closed: freezed == closed
                ? _value.closed
                : closed // ignore: cast_nullable_to_non_nullable
                      as String?,
          )
          as $Val,
    );
  }

  /// Create a copy of SubIssueModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SimpleProjectModelCopyWith<$Res> get project {
    return $SimpleProjectModelCopyWith<$Res>(_value.project, (value) {
      return _then(_value.copyWith(project: value) as $Val);
    });
  }

  /// Create a copy of SubIssueModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $IssueTrackerModelCopyWith<$Res> get tracker {
    return $IssueTrackerModelCopyWith<$Res>(_value.tracker, (value) {
      return _then(_value.copyWith(tracker: value) as $Val);
    });
  }

  /// Create a copy of SubIssueModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SimpleUserModelCopyWith<$Res>? get assignedTo {
    if (_value.assignedTo == null) {
      return null;
    }

    return $SimpleUserModelCopyWith<$Res>(_value.assignedTo!, (value) {
      return _then(_value.copyWith(assignedTo: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$SubIssueModelImplCopyWith<$Res>
    implements $SubIssueModelCopyWith<$Res> {
  factory _$$SubIssueModelImplCopyWith(
    _$SubIssueModelImpl value,
    $Res Function(_$SubIssueModelImpl) then,
  ) = __$$SubIssueModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int pk,
    SimpleProjectModel project,
    String subject,
    IssueTrackerModel tracker,
    String status,
    SimpleUserModel? assignedTo,
    List<SimpleUserModel> watchers,
    int? priority,
    String? startDate,
    String? dueDate,
    int doneRatio,
    String? closed,
  });

  @override
  $SimpleProjectModelCopyWith<$Res> get project;
  @override
  $IssueTrackerModelCopyWith<$Res> get tracker;
  @override
  $SimpleUserModelCopyWith<$Res>? get assignedTo;
}

/// @nodoc
class __$$SubIssueModelImplCopyWithImpl<$Res>
    extends _$SubIssueModelCopyWithImpl<$Res, _$SubIssueModelImpl>
    implements _$$SubIssueModelImplCopyWith<$Res> {
  __$$SubIssueModelImplCopyWithImpl(
    _$SubIssueModelImpl _value,
    $Res Function(_$SubIssueModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of SubIssueModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? project = null,
    Object? subject = null,
    Object? tracker = null,
    Object? status = null,
    Object? assignedTo = freezed,
    Object? watchers = null,
    Object? priority = freezed,
    Object? startDate = freezed,
    Object? dueDate = freezed,
    Object? doneRatio = null,
    Object? closed = freezed,
  }) {
    return _then(
      _$SubIssueModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        project: null == project
            ? _value.project
            : project // ignore: cast_nullable_to_non_nullable
                  as SimpleProjectModel,
        subject: null == subject
            ? _value.subject
            : subject // ignore: cast_nullable_to_non_nullable
                  as String,
        tracker: null == tracker
            ? _value.tracker
            : tracker // ignore: cast_nullable_to_non_nullable
                  as IssueTrackerModel,
        status: null == status
            ? _value.status
            : status // ignore: cast_nullable_to_non_nullable
                  as String,
        assignedTo: freezed == assignedTo
            ? _value.assignedTo
            : assignedTo // ignore: cast_nullable_to_non_nullable
                  as SimpleUserModel?,
        watchers: null == watchers
            ? _value._watchers
            : watchers // ignore: cast_nullable_to_non_nullable
                  as List<SimpleUserModel>,
        priority: freezed == priority
            ? _value.priority
            : priority // ignore: cast_nullable_to_non_nullable
                  as int?,
        startDate: freezed == startDate
            ? _value.startDate
            : startDate // ignore: cast_nullable_to_non_nullable
                  as String?,
        dueDate: freezed == dueDate
            ? _value.dueDate
            : dueDate // ignore: cast_nullable_to_non_nullable
                  as String?,
        doneRatio: null == doneRatio
            ? _value.doneRatio
            : doneRatio // ignore: cast_nullable_to_non_nullable
                  as int,
        closed: freezed == closed
            ? _value.closed
            : closed // ignore: cast_nullable_to_non_nullable
                  as String?,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$SubIssueModelImpl implements _SubIssueModel {
  const _$SubIssueModelImpl({
    required this.pk,
    required this.project,
    required this.subject,
    required this.tracker,
    required this.status,
    this.assignedTo,
    final List<SimpleUserModel> watchers = const [],
    this.priority,
    this.startDate,
    this.dueDate,
    this.doneRatio = 0,
    this.closed,
  }) : _watchers = watchers;

  factory _$SubIssueModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$SubIssueModelImplFromJson(json);

  @override
  final int pk;
  @override
  final SimpleProjectModel project;
  @override
  final String subject;
  @override
  final IssueTrackerModel tracker;
  @override
  final String status;
  @override
  final SimpleUserModel? assignedTo;
  final List<SimpleUserModel> _watchers;
  @override
  @JsonKey()
  List<SimpleUserModel> get watchers {
    if (_watchers is EqualUnmodifiableListView) return _watchers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_watchers);
  }

  @override
  final int? priority;
  @override
  final String? startDate;
  @override
  final String? dueDate;
  @override
  @JsonKey()
  final int doneRatio;
  @override
  final String? closed;

  @override
  String toString() {
    return 'SubIssueModel(pk: $pk, project: $project, subject: $subject, tracker: $tracker, status: $status, assignedTo: $assignedTo, watchers: $watchers, priority: $priority, startDate: $startDate, dueDate: $dueDate, doneRatio: $doneRatio, closed: $closed)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SubIssueModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.project, project) || other.project == project) &&
            (identical(other.subject, subject) || other.subject == subject) &&
            (identical(other.tracker, tracker) || other.tracker == tracker) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.assignedTo, assignedTo) ||
                other.assignedTo == assignedTo) &&
            const DeepCollectionEquality().equals(other._watchers, _watchers) &&
            (identical(other.priority, priority) ||
                other.priority == priority) &&
            (identical(other.startDate, startDate) ||
                other.startDate == startDate) &&
            (identical(other.dueDate, dueDate) || other.dueDate == dueDate) &&
            (identical(other.doneRatio, doneRatio) ||
                other.doneRatio == doneRatio) &&
            (identical(other.closed, closed) || other.closed == closed));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
    runtimeType,
    pk,
    project,
    subject,
    tracker,
    status,
    assignedTo,
    const DeepCollectionEquality().hash(_watchers),
    priority,
    startDate,
    dueDate,
    doneRatio,
    closed,
  );

  /// Create a copy of SubIssueModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$SubIssueModelImplCopyWith<_$SubIssueModelImpl> get copyWith =>
      __$$SubIssueModelImplCopyWithImpl<_$SubIssueModelImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$SubIssueModelImplToJson(this);
  }
}

abstract class _SubIssueModel implements SubIssueModel {
  const factory _SubIssueModel({
    required final int pk,
    required final SimpleProjectModel project,
    required final String subject,
    required final IssueTrackerModel tracker,
    required final String status,
    final SimpleUserModel? assignedTo,
    final List<SimpleUserModel> watchers,
    final int? priority,
    final String? startDate,
    final String? dueDate,
    final int doneRatio,
    final String? closed,
  }) = _$SubIssueModelImpl;

  factory _SubIssueModel.fromJson(Map<String, dynamic> json) =
      _$SubIssueModelImpl.fromJson;

  @override
  int get pk;
  @override
  SimpleProjectModel get project;
  @override
  String get subject;
  @override
  IssueTrackerModel get tracker;
  @override
  String get status;
  @override
  SimpleUserModel? get assignedTo;
  @override
  List<SimpleUserModel> get watchers;
  @override
  int? get priority;
  @override
  String? get startDate;
  @override
  String? get dueDate;
  @override
  int get doneRatio;
  @override
  String? get closed;

  /// Create a copy of SubIssueModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$SubIssueModelImplCopyWith<_$SubIssueModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

IssueInRelationModel _$IssueInRelationModelFromJson(Map<String, dynamic> json) {
  return _IssueInRelationModel.fromJson(json);
}

/// @nodoc
mixin _$IssueInRelationModel {
  int get pk => throw _privateConstructorUsedError;
  SimpleProjectModel get project => throw _privateConstructorUsedError;
  String get subject => throw _privateConstructorUsedError;
  IssueTrackerModel get tracker => throw _privateConstructorUsedError;
  String get status => throw _privateConstructorUsedError;
  SimpleUserModel? get assignedTo => throw _privateConstructorUsedError;
  List<SimpleUserModel> get watchers => throw _privateConstructorUsedError;
  int? get priority => throw _privateConstructorUsedError;
  String? get startDate => throw _privateConstructorUsedError;
  String? get dueDate => throw _privateConstructorUsedError;
  int get doneRatio => throw _privateConstructorUsedError;
  String? get closed => throw _privateConstructorUsedError;

  /// Serializes this IssueInRelationModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of IssueInRelationModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $IssueInRelationModelCopyWith<IssueInRelationModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $IssueInRelationModelCopyWith<$Res> {
  factory $IssueInRelationModelCopyWith(
    IssueInRelationModel value,
    $Res Function(IssueInRelationModel) then,
  ) = _$IssueInRelationModelCopyWithImpl<$Res, IssueInRelationModel>;
  @useResult
  $Res call({
    int pk,
    SimpleProjectModel project,
    String subject,
    IssueTrackerModel tracker,
    String status,
    SimpleUserModel? assignedTo,
    List<SimpleUserModel> watchers,
    int? priority,
    String? startDate,
    String? dueDate,
    int doneRatio,
    String? closed,
  });

  $SimpleProjectModelCopyWith<$Res> get project;
  $IssueTrackerModelCopyWith<$Res> get tracker;
  $SimpleUserModelCopyWith<$Res>? get assignedTo;
}

/// @nodoc
class _$IssueInRelationModelCopyWithImpl<
  $Res,
  $Val extends IssueInRelationModel
>
    implements $IssueInRelationModelCopyWith<$Res> {
  _$IssueInRelationModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of IssueInRelationModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? project = null,
    Object? subject = null,
    Object? tracker = null,
    Object? status = null,
    Object? assignedTo = freezed,
    Object? watchers = null,
    Object? priority = freezed,
    Object? startDate = freezed,
    Object? dueDate = freezed,
    Object? doneRatio = null,
    Object? closed = freezed,
  }) {
    return _then(
      _value.copyWith(
            pk: null == pk
                ? _value.pk
                : pk // ignore: cast_nullable_to_non_nullable
                      as int,
            project: null == project
                ? _value.project
                : project // ignore: cast_nullable_to_non_nullable
                      as SimpleProjectModel,
            subject: null == subject
                ? _value.subject
                : subject // ignore: cast_nullable_to_non_nullable
                      as String,
            tracker: null == tracker
                ? _value.tracker
                : tracker // ignore: cast_nullable_to_non_nullable
                      as IssueTrackerModel,
            status: null == status
                ? _value.status
                : status // ignore: cast_nullable_to_non_nullable
                      as String,
            assignedTo: freezed == assignedTo
                ? _value.assignedTo
                : assignedTo // ignore: cast_nullable_to_non_nullable
                      as SimpleUserModel?,
            watchers: null == watchers
                ? _value.watchers
                : watchers // ignore: cast_nullable_to_non_nullable
                      as List<SimpleUserModel>,
            priority: freezed == priority
                ? _value.priority
                : priority // ignore: cast_nullable_to_non_nullable
                      as int?,
            startDate: freezed == startDate
                ? _value.startDate
                : startDate // ignore: cast_nullable_to_non_nullable
                      as String?,
            dueDate: freezed == dueDate
                ? _value.dueDate
                : dueDate // ignore: cast_nullable_to_non_nullable
                      as String?,
            doneRatio: null == doneRatio
                ? _value.doneRatio
                : doneRatio // ignore: cast_nullable_to_non_nullable
                      as int,
            closed: freezed == closed
                ? _value.closed
                : closed // ignore: cast_nullable_to_non_nullable
                      as String?,
          )
          as $Val,
    );
  }

  /// Create a copy of IssueInRelationModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SimpleProjectModelCopyWith<$Res> get project {
    return $SimpleProjectModelCopyWith<$Res>(_value.project, (value) {
      return _then(_value.copyWith(project: value) as $Val);
    });
  }

  /// Create a copy of IssueInRelationModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $IssueTrackerModelCopyWith<$Res> get tracker {
    return $IssueTrackerModelCopyWith<$Res>(_value.tracker, (value) {
      return _then(_value.copyWith(tracker: value) as $Val);
    });
  }

  /// Create a copy of IssueInRelationModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SimpleUserModelCopyWith<$Res>? get assignedTo {
    if (_value.assignedTo == null) {
      return null;
    }

    return $SimpleUserModelCopyWith<$Res>(_value.assignedTo!, (value) {
      return _then(_value.copyWith(assignedTo: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$IssueInRelationModelImplCopyWith<$Res>
    implements $IssueInRelationModelCopyWith<$Res> {
  factory _$$IssueInRelationModelImplCopyWith(
    _$IssueInRelationModelImpl value,
    $Res Function(_$IssueInRelationModelImpl) then,
  ) = __$$IssueInRelationModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int pk,
    SimpleProjectModel project,
    String subject,
    IssueTrackerModel tracker,
    String status,
    SimpleUserModel? assignedTo,
    List<SimpleUserModel> watchers,
    int? priority,
    String? startDate,
    String? dueDate,
    int doneRatio,
    String? closed,
  });

  @override
  $SimpleProjectModelCopyWith<$Res> get project;
  @override
  $IssueTrackerModelCopyWith<$Res> get tracker;
  @override
  $SimpleUserModelCopyWith<$Res>? get assignedTo;
}

/// @nodoc
class __$$IssueInRelationModelImplCopyWithImpl<$Res>
    extends _$IssueInRelationModelCopyWithImpl<$Res, _$IssueInRelationModelImpl>
    implements _$$IssueInRelationModelImplCopyWith<$Res> {
  __$$IssueInRelationModelImplCopyWithImpl(
    _$IssueInRelationModelImpl _value,
    $Res Function(_$IssueInRelationModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of IssueInRelationModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? project = null,
    Object? subject = null,
    Object? tracker = null,
    Object? status = null,
    Object? assignedTo = freezed,
    Object? watchers = null,
    Object? priority = freezed,
    Object? startDate = freezed,
    Object? dueDate = freezed,
    Object? doneRatio = null,
    Object? closed = freezed,
  }) {
    return _then(
      _$IssueInRelationModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        project: null == project
            ? _value.project
            : project // ignore: cast_nullable_to_non_nullable
                  as SimpleProjectModel,
        subject: null == subject
            ? _value.subject
            : subject // ignore: cast_nullable_to_non_nullable
                  as String,
        tracker: null == tracker
            ? _value.tracker
            : tracker // ignore: cast_nullable_to_non_nullable
                  as IssueTrackerModel,
        status: null == status
            ? _value.status
            : status // ignore: cast_nullable_to_non_nullable
                  as String,
        assignedTo: freezed == assignedTo
            ? _value.assignedTo
            : assignedTo // ignore: cast_nullable_to_non_nullable
                  as SimpleUserModel?,
        watchers: null == watchers
            ? _value._watchers
            : watchers // ignore: cast_nullable_to_non_nullable
                  as List<SimpleUserModel>,
        priority: freezed == priority
            ? _value.priority
            : priority // ignore: cast_nullable_to_non_nullable
                  as int?,
        startDate: freezed == startDate
            ? _value.startDate
            : startDate // ignore: cast_nullable_to_non_nullable
                  as String?,
        dueDate: freezed == dueDate
            ? _value.dueDate
            : dueDate // ignore: cast_nullable_to_non_nullable
                  as String?,
        doneRatio: null == doneRatio
            ? _value.doneRatio
            : doneRatio // ignore: cast_nullable_to_non_nullable
                  as int,
        closed: freezed == closed
            ? _value.closed
            : closed // ignore: cast_nullable_to_non_nullable
                  as String?,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$IssueInRelationModelImpl implements _IssueInRelationModel {
  const _$IssueInRelationModelImpl({
    required this.pk,
    required this.project,
    required this.subject,
    required this.tracker,
    required this.status,
    this.assignedTo,
    final List<SimpleUserModel> watchers = const [],
    this.priority,
    this.startDate,
    this.dueDate,
    this.doneRatio = 0,
    this.closed,
  }) : _watchers = watchers;

  factory _$IssueInRelationModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$IssueInRelationModelImplFromJson(json);

  @override
  final int pk;
  @override
  final SimpleProjectModel project;
  @override
  final String subject;
  @override
  final IssueTrackerModel tracker;
  @override
  final String status;
  @override
  final SimpleUserModel? assignedTo;
  final List<SimpleUserModel> _watchers;
  @override
  @JsonKey()
  List<SimpleUserModel> get watchers {
    if (_watchers is EqualUnmodifiableListView) return _watchers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_watchers);
  }

  @override
  final int? priority;
  @override
  final String? startDate;
  @override
  final String? dueDate;
  @override
  @JsonKey()
  final int doneRatio;
  @override
  final String? closed;

  @override
  String toString() {
    return 'IssueInRelationModel(pk: $pk, project: $project, subject: $subject, tracker: $tracker, status: $status, assignedTo: $assignedTo, watchers: $watchers, priority: $priority, startDate: $startDate, dueDate: $dueDate, doneRatio: $doneRatio, closed: $closed)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$IssueInRelationModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.project, project) || other.project == project) &&
            (identical(other.subject, subject) || other.subject == subject) &&
            (identical(other.tracker, tracker) || other.tracker == tracker) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.assignedTo, assignedTo) ||
                other.assignedTo == assignedTo) &&
            const DeepCollectionEquality().equals(other._watchers, _watchers) &&
            (identical(other.priority, priority) ||
                other.priority == priority) &&
            (identical(other.startDate, startDate) ||
                other.startDate == startDate) &&
            (identical(other.dueDate, dueDate) || other.dueDate == dueDate) &&
            (identical(other.doneRatio, doneRatio) ||
                other.doneRatio == doneRatio) &&
            (identical(other.closed, closed) || other.closed == closed));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
    runtimeType,
    pk,
    project,
    subject,
    tracker,
    status,
    assignedTo,
    const DeepCollectionEquality().hash(_watchers),
    priority,
    startDate,
    dueDate,
    doneRatio,
    closed,
  );

  /// Create a copy of IssueInRelationModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$IssueInRelationModelImplCopyWith<_$IssueInRelationModelImpl>
  get copyWith =>
      __$$IssueInRelationModelImplCopyWithImpl<_$IssueInRelationModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$IssueInRelationModelImplToJson(this);
  }
}

abstract class _IssueInRelationModel implements IssueInRelationModel {
  const factory _IssueInRelationModel({
    required final int pk,
    required final SimpleProjectModel project,
    required final String subject,
    required final IssueTrackerModel tracker,
    required final String status,
    final SimpleUserModel? assignedTo,
    final List<SimpleUserModel> watchers,
    final int? priority,
    final String? startDate,
    final String? dueDate,
    final int doneRatio,
    final String? closed,
  }) = _$IssueInRelationModelImpl;

  factory _IssueInRelationModel.fromJson(Map<String, dynamic> json) =
      _$IssueInRelationModelImpl.fromJson;

  @override
  int get pk;
  @override
  SimpleProjectModel get project;
  @override
  String get subject;
  @override
  IssueTrackerModel get tracker;
  @override
  String get status;
  @override
  SimpleUserModel? get assignedTo;
  @override
  List<SimpleUserModel> get watchers;
  @override
  int? get priority;
  @override
  String? get startDate;
  @override
  String? get dueDate;
  @override
  int get doneRatio;
  @override
  String? get closed;

  /// Create a copy of IssueInRelationModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$IssueInRelationModelImplCopyWith<_$IssueInRelationModelImpl>
  get copyWith => throw _privateConstructorUsedError;
}

IssueRelationModel _$IssueRelationModelFromJson(Map<String, dynamic> json) {
  return _IssueRelationModel.fromJson(json);
}

/// @nodoc
mixin _$IssueRelationModel {
  int? get pk => throw _privateConstructorUsedError;
  IssueInRelationModel? get issue => throw _privateConstructorUsedError;
  int? get delay => throw _privateConstructorUsedError;

  /// Serializes this IssueRelationModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of IssueRelationModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $IssueRelationModelCopyWith<IssueRelationModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $IssueRelationModelCopyWith<$Res> {
  factory $IssueRelationModelCopyWith(
    IssueRelationModel value,
    $Res Function(IssueRelationModel) then,
  ) = _$IssueRelationModelCopyWithImpl<$Res, IssueRelationModel>;
  @useResult
  $Res call({int? pk, IssueInRelationModel? issue, int? delay});

  $IssueInRelationModelCopyWith<$Res>? get issue;
}

/// @nodoc
class _$IssueRelationModelCopyWithImpl<$Res, $Val extends IssueRelationModel>
    implements $IssueRelationModelCopyWith<$Res> {
  _$IssueRelationModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of IssueRelationModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = freezed,
    Object? issue = freezed,
    Object? delay = freezed,
  }) {
    return _then(
      _value.copyWith(
            pk: freezed == pk
                ? _value.pk
                : pk // ignore: cast_nullable_to_non_nullable
                      as int?,
            issue: freezed == issue
                ? _value.issue
                : issue // ignore: cast_nullable_to_non_nullable
                      as IssueInRelationModel?,
            delay: freezed == delay
                ? _value.delay
                : delay // ignore: cast_nullable_to_non_nullable
                      as int?,
          )
          as $Val,
    );
  }

  /// Create a copy of IssueRelationModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $IssueInRelationModelCopyWith<$Res>? get issue {
    if (_value.issue == null) {
      return null;
    }

    return $IssueInRelationModelCopyWith<$Res>(_value.issue!, (value) {
      return _then(_value.copyWith(issue: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$IssueRelationModelImplCopyWith<$Res>
    implements $IssueRelationModelCopyWith<$Res> {
  factory _$$IssueRelationModelImplCopyWith(
    _$IssueRelationModelImpl value,
    $Res Function(_$IssueRelationModelImpl) then,
  ) = __$$IssueRelationModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({int? pk, IssueInRelationModel? issue, int? delay});

  @override
  $IssueInRelationModelCopyWith<$Res>? get issue;
}

/// @nodoc
class __$$IssueRelationModelImplCopyWithImpl<$Res>
    extends _$IssueRelationModelCopyWithImpl<$Res, _$IssueRelationModelImpl>
    implements _$$IssueRelationModelImplCopyWith<$Res> {
  __$$IssueRelationModelImplCopyWithImpl(
    _$IssueRelationModelImpl _value,
    $Res Function(_$IssueRelationModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of IssueRelationModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = freezed,
    Object? issue = freezed,
    Object? delay = freezed,
  }) {
    return _then(
      _$IssueRelationModelImpl(
        pk: freezed == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int?,
        issue: freezed == issue
            ? _value.issue
            : issue // ignore: cast_nullable_to_non_nullable
                  as IssueInRelationModel?,
        delay: freezed == delay
            ? _value.delay
            : delay // ignore: cast_nullable_to_non_nullable
                  as int?,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$IssueRelationModelImpl implements _IssueRelationModel {
  const _$IssueRelationModelImpl({this.pk, this.issue, this.delay});

  factory _$IssueRelationModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$IssueRelationModelImplFromJson(json);

  @override
  final int? pk;
  @override
  final IssueInRelationModel? issue;
  @override
  final int? delay;

  @override
  String toString() {
    return 'IssueRelationModel(pk: $pk, issue: $issue, delay: $delay)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$IssueRelationModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.issue, issue) || other.issue == issue) &&
            (identical(other.delay, delay) || other.delay == delay));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, pk, issue, delay);

  /// Create a copy of IssueRelationModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$IssueRelationModelImplCopyWith<_$IssueRelationModelImpl> get copyWith =>
      __$$IssueRelationModelImplCopyWithImpl<_$IssueRelationModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$IssueRelationModelImplToJson(this);
  }
}

abstract class _IssueRelationModel implements IssueRelationModel {
  const factory _IssueRelationModel({
    final int? pk,
    final IssueInRelationModel? issue,
    final int? delay,
  }) = _$IssueRelationModelImpl;

  factory _IssueRelationModel.fromJson(Map<String, dynamic> json) =
      _$IssueRelationModelImpl.fromJson;

  @override
  int? get pk;
  @override
  IssueInRelationModel? get issue;
  @override
  int? get delay;

  /// Create a copy of IssueRelationModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$IssueRelationModelImplCopyWith<_$IssueRelationModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

IssueCommentModel _$IssueCommentModelFromJson(Map<String, dynamic> json) {
  return _IssueCommentModel.fromJson(json);
}

/// @nodoc
mixin _$IssueCommentModel {
  int get pk => throw _privateConstructorUsedError;
  String get content => throw _privateConstructorUsedError;
  bool get isPrivate => throw _privateConstructorUsedError;
  bool get isBlocked => throw _privateConstructorUsedError;
  String get created => throw _privateConstructorUsedError;
  String get updated => throw _privateConstructorUsedError;
  SimpleUserModel get creator => throw _privateConstructorUsedError;

  /// Serializes this IssueCommentModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of IssueCommentModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $IssueCommentModelCopyWith<IssueCommentModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $IssueCommentModelCopyWith<$Res> {
  factory $IssueCommentModelCopyWith(
    IssueCommentModel value,
    $Res Function(IssueCommentModel) then,
  ) = _$IssueCommentModelCopyWithImpl<$Res, IssueCommentModel>;
  @useResult
  $Res call({
    int pk,
    String content,
    bool isPrivate,
    bool isBlocked,
    String created,
    String updated,
    SimpleUserModel creator,
  });

  $SimpleUserModelCopyWith<$Res> get creator;
}

/// @nodoc
class _$IssueCommentModelCopyWithImpl<$Res, $Val extends IssueCommentModel>
    implements $IssueCommentModelCopyWith<$Res> {
  _$IssueCommentModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of IssueCommentModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? content = null,
    Object? isPrivate = null,
    Object? isBlocked = null,
    Object? created = null,
    Object? updated = null,
    Object? creator = null,
  }) {
    return _then(
      _value.copyWith(
            pk: null == pk
                ? _value.pk
                : pk // ignore: cast_nullable_to_non_nullable
                      as int,
            content: null == content
                ? _value.content
                : content // ignore: cast_nullable_to_non_nullable
                      as String,
            isPrivate: null == isPrivate
                ? _value.isPrivate
                : isPrivate // ignore: cast_nullable_to_non_nullable
                      as bool,
            isBlocked: null == isBlocked
                ? _value.isBlocked
                : isBlocked // ignore: cast_nullable_to_non_nullable
                      as bool,
            created: null == created
                ? _value.created
                : created // ignore: cast_nullable_to_non_nullable
                      as String,
            updated: null == updated
                ? _value.updated
                : updated // ignore: cast_nullable_to_non_nullable
                      as String,
            creator: null == creator
                ? _value.creator
                : creator // ignore: cast_nullable_to_non_nullable
                      as SimpleUserModel,
          )
          as $Val,
    );
  }

  /// Create a copy of IssueCommentModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SimpleUserModelCopyWith<$Res> get creator {
    return $SimpleUserModelCopyWith<$Res>(_value.creator, (value) {
      return _then(_value.copyWith(creator: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$IssueCommentModelImplCopyWith<$Res>
    implements $IssueCommentModelCopyWith<$Res> {
  factory _$$IssueCommentModelImplCopyWith(
    _$IssueCommentModelImpl value,
    $Res Function(_$IssueCommentModelImpl) then,
  ) = __$$IssueCommentModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int pk,
    String content,
    bool isPrivate,
    bool isBlocked,
    String created,
    String updated,
    SimpleUserModel creator,
  });

  @override
  $SimpleUserModelCopyWith<$Res> get creator;
}

/// @nodoc
class __$$IssueCommentModelImplCopyWithImpl<$Res>
    extends _$IssueCommentModelCopyWithImpl<$Res, _$IssueCommentModelImpl>
    implements _$$IssueCommentModelImplCopyWith<$Res> {
  __$$IssueCommentModelImplCopyWithImpl(
    _$IssueCommentModelImpl _value,
    $Res Function(_$IssueCommentModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of IssueCommentModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? content = null,
    Object? isPrivate = null,
    Object? isBlocked = null,
    Object? created = null,
    Object? updated = null,
    Object? creator = null,
  }) {
    return _then(
      _$IssueCommentModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        content: null == content
            ? _value.content
            : content // ignore: cast_nullable_to_non_nullable
                  as String,
        isPrivate: null == isPrivate
            ? _value.isPrivate
            : isPrivate // ignore: cast_nullable_to_non_nullable
                  as bool,
        isBlocked: null == isBlocked
            ? _value.isBlocked
            : isBlocked // ignore: cast_nullable_to_non_nullable
                  as bool,
        created: null == created
            ? _value.created
            : created // ignore: cast_nullable_to_non_nullable
                  as String,
        updated: null == updated
            ? _value.updated
            : updated // ignore: cast_nullable_to_non_nullable
                  as String,
        creator: null == creator
            ? _value.creator
            : creator // ignore: cast_nullable_to_non_nullable
                  as SimpleUserModel,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$IssueCommentModelImpl implements _IssueCommentModel {
  const _$IssueCommentModelImpl({
    required this.pk,
    required this.content,
    this.isPrivate = false,
    this.isBlocked = false,
    required this.created,
    required this.updated,
    required this.creator,
  });

  factory _$IssueCommentModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$IssueCommentModelImplFromJson(json);

  @override
  final int pk;
  @override
  final String content;
  @override
  @JsonKey()
  final bool isPrivate;
  @override
  @JsonKey()
  final bool isBlocked;
  @override
  final String created;
  @override
  final String updated;
  @override
  final SimpleUserModel creator;

  @override
  String toString() {
    return 'IssueCommentModel(pk: $pk, content: $content, isPrivate: $isPrivate, isBlocked: $isBlocked, created: $created, updated: $updated, creator: $creator)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$IssueCommentModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.content, content) || other.content == content) &&
            (identical(other.isPrivate, isPrivate) ||
                other.isPrivate == isPrivate) &&
            (identical(other.isBlocked, isBlocked) ||
                other.isBlocked == isBlocked) &&
            (identical(other.created, created) || other.created == created) &&
            (identical(other.updated, updated) || other.updated == updated) &&
            (identical(other.creator, creator) || other.creator == creator));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
    runtimeType,
    pk,
    content,
    isPrivate,
    isBlocked,
    created,
    updated,
    creator,
  );

  /// Create a copy of IssueCommentModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$IssueCommentModelImplCopyWith<_$IssueCommentModelImpl> get copyWith =>
      __$$IssueCommentModelImplCopyWithImpl<_$IssueCommentModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$IssueCommentModelImplToJson(this);
  }
}

abstract class _IssueCommentModel implements IssueCommentModel {
  const factory _IssueCommentModel({
    required final int pk,
    required final String content,
    final bool isPrivate,
    final bool isBlocked,
    required final String created,
    required final String updated,
    required final SimpleUserModel creator,
  }) = _$IssueCommentModelImpl;

  factory _IssueCommentModel.fromJson(Map<String, dynamic> json) =
      _$IssueCommentModelImpl.fromJson;

  @override
  int get pk;
  @override
  String get content;
  @override
  bool get isPrivate;
  @override
  bool get isBlocked;
  @override
  String get created;
  @override
  String get updated;
  @override
  SimpleUserModel get creator;

  /// Create a copy of IssueCommentModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$IssueCommentModelImplCopyWith<_$IssueCommentModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

IssueModel _$IssueModelFromJson(Map<String, dynamic> json) {
  return _IssueModel.fromJson(json);
}

/// @nodoc
mixin _$IssueModel {
  int get pk => throw _privateConstructorUsedError;
  SimpleProjectModel get project => throw _privateConstructorUsedError;
  IssueTrackerModel get tracker => throw _privateConstructorUsedError;
  IssueStatusModel get status => throw _privateConstructorUsedError;
  IssuePriorityModel get priority => throw _privateConstructorUsedError;
  String get subject => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  int? get category => throw _privateConstructorUsedError;
  IssueVersionModel? get fixedVersion => throw _privateConstructorUsedError;
  SimpleUserModel? get assignedTo => throw _privateConstructorUsedError;
  ParentIssueModel? get parent => throw _privateConstructorUsedError;
  List<SimpleUserModel> get watchers => throw _privateConstructorUsedError;
  bool get isPrivate => throw _privateConstructorUsedError;
  String? get expectedDuration => throw _privateConstructorUsedError;
  String get expectedDurationDisplay => throw _privateConstructorUsedError;
  String get startDate => throw _privateConstructorUsedError;
  String? get dueDate => throw _privateConstructorUsedError;
  int? get meeting => throw _privateConstructorUsedError;
  MeetingDescModel? get meetingDesc => throw _privateConstructorUsedError;
  int get doneRatio => throw _privateConstructorUsedError;
  String? get closed => throw _privateConstructorUsedError;
  List<IssueFileModel> get files => throw _privateConstructorUsedError;
  List<IssueLinkModel> get links => throw _privateConstructorUsedError;
  List<SubIssueModel> get subIssues => throw _privateConstructorUsedError;
  List<IssueRelationModel> get outgoingRelations =>
      throw _privateConstructorUsedError;
  IssueRelationModel? get incomingRelation =>
      throw _privateConstructorUsedError;
  SimpleUserModel? get creator => throw _privateConstructorUsedError;
  int? get updater => throw _privateConstructorUsedError;
  String get created => throw _privateConstructorUsedError;
  String get updated => throw _privateConstructorUsedError;

  /// Serializes this IssueModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of IssueModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $IssueModelCopyWith<IssueModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $IssueModelCopyWith<$Res> {
  factory $IssueModelCopyWith(
    IssueModel value,
    $Res Function(IssueModel) then,
  ) = _$IssueModelCopyWithImpl<$Res, IssueModel>;
  @useResult
  $Res call({
    int pk,
    SimpleProjectModel project,
    IssueTrackerModel tracker,
    IssueStatusModel status,
    IssuePriorityModel priority,
    String subject,
    String description,
    int? category,
    IssueVersionModel? fixedVersion,
    SimpleUserModel? assignedTo,
    ParentIssueModel? parent,
    List<SimpleUserModel> watchers,
    bool isPrivate,
    String? expectedDuration,
    String expectedDurationDisplay,
    String startDate,
    String? dueDate,
    int? meeting,
    MeetingDescModel? meetingDesc,
    int doneRatio,
    String? closed,
    List<IssueFileModel> files,
    List<IssueLinkModel> links,
    List<SubIssueModel> subIssues,
    List<IssueRelationModel> outgoingRelations,
    IssueRelationModel? incomingRelation,
    SimpleUserModel? creator,
    int? updater,
    String created,
    String updated,
  });

  $SimpleProjectModelCopyWith<$Res> get project;
  $IssueTrackerModelCopyWith<$Res> get tracker;
  $IssueStatusModelCopyWith<$Res> get status;
  $IssuePriorityModelCopyWith<$Res> get priority;
  $IssueVersionModelCopyWith<$Res>? get fixedVersion;
  $SimpleUserModelCopyWith<$Res>? get assignedTo;
  $ParentIssueModelCopyWith<$Res>? get parent;
  $MeetingDescModelCopyWith<$Res>? get meetingDesc;
  $IssueRelationModelCopyWith<$Res>? get incomingRelation;
  $SimpleUserModelCopyWith<$Res>? get creator;
}

/// @nodoc
class _$IssueModelCopyWithImpl<$Res, $Val extends IssueModel>
    implements $IssueModelCopyWith<$Res> {
  _$IssueModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of IssueModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? project = null,
    Object? tracker = null,
    Object? status = null,
    Object? priority = null,
    Object? subject = null,
    Object? description = null,
    Object? category = freezed,
    Object? fixedVersion = freezed,
    Object? assignedTo = freezed,
    Object? parent = freezed,
    Object? watchers = null,
    Object? isPrivate = null,
    Object? expectedDuration = freezed,
    Object? expectedDurationDisplay = null,
    Object? startDate = null,
    Object? dueDate = freezed,
    Object? meeting = freezed,
    Object? meetingDesc = freezed,
    Object? doneRatio = null,
    Object? closed = freezed,
    Object? files = null,
    Object? links = null,
    Object? subIssues = null,
    Object? outgoingRelations = null,
    Object? incomingRelation = freezed,
    Object? creator = freezed,
    Object? updater = freezed,
    Object? created = null,
    Object? updated = null,
  }) {
    return _then(
      _value.copyWith(
            pk: null == pk
                ? _value.pk
                : pk // ignore: cast_nullable_to_non_nullable
                      as int,
            project: null == project
                ? _value.project
                : project // ignore: cast_nullable_to_non_nullable
                      as SimpleProjectModel,
            tracker: null == tracker
                ? _value.tracker
                : tracker // ignore: cast_nullable_to_non_nullable
                      as IssueTrackerModel,
            status: null == status
                ? _value.status
                : status // ignore: cast_nullable_to_non_nullable
                      as IssueStatusModel,
            priority: null == priority
                ? _value.priority
                : priority // ignore: cast_nullable_to_non_nullable
                      as IssuePriorityModel,
            subject: null == subject
                ? _value.subject
                : subject // ignore: cast_nullable_to_non_nullable
                      as String,
            description: null == description
                ? _value.description
                : description // ignore: cast_nullable_to_non_nullable
                      as String,
            category: freezed == category
                ? _value.category
                : category // ignore: cast_nullable_to_non_nullable
                      as int?,
            fixedVersion: freezed == fixedVersion
                ? _value.fixedVersion
                : fixedVersion // ignore: cast_nullable_to_non_nullable
                      as IssueVersionModel?,
            assignedTo: freezed == assignedTo
                ? _value.assignedTo
                : assignedTo // ignore: cast_nullable_to_non_nullable
                      as SimpleUserModel?,
            parent: freezed == parent
                ? _value.parent
                : parent // ignore: cast_nullable_to_non_nullable
                      as ParentIssueModel?,
            watchers: null == watchers
                ? _value.watchers
                : watchers // ignore: cast_nullable_to_non_nullable
                      as List<SimpleUserModel>,
            isPrivate: null == isPrivate
                ? _value.isPrivate
                : isPrivate // ignore: cast_nullable_to_non_nullable
                      as bool,
            expectedDuration: freezed == expectedDuration
                ? _value.expectedDuration
                : expectedDuration // ignore: cast_nullable_to_non_nullable
                      as String?,
            expectedDurationDisplay: null == expectedDurationDisplay
                ? _value.expectedDurationDisplay
                : expectedDurationDisplay // ignore: cast_nullable_to_non_nullable
                      as String,
            startDate: null == startDate
                ? _value.startDate
                : startDate // ignore: cast_nullable_to_non_nullable
                      as String,
            dueDate: freezed == dueDate
                ? _value.dueDate
                : dueDate // ignore: cast_nullable_to_non_nullable
                      as String?,
            meeting: freezed == meeting
                ? _value.meeting
                : meeting // ignore: cast_nullable_to_non_nullable
                      as int?,
            meetingDesc: freezed == meetingDesc
                ? _value.meetingDesc
                : meetingDesc // ignore: cast_nullable_to_non_nullable
                      as MeetingDescModel?,
            doneRatio: null == doneRatio
                ? _value.doneRatio
                : doneRatio // ignore: cast_nullable_to_non_nullable
                      as int,
            closed: freezed == closed
                ? _value.closed
                : closed // ignore: cast_nullable_to_non_nullable
                      as String?,
            files: null == files
                ? _value.files
                : files // ignore: cast_nullable_to_non_nullable
                      as List<IssueFileModel>,
            links: null == links
                ? _value.links
                : links // ignore: cast_nullable_to_non_nullable
                      as List<IssueLinkModel>,
            subIssues: null == subIssues
                ? _value.subIssues
                : subIssues // ignore: cast_nullable_to_non_nullable
                      as List<SubIssueModel>,
            outgoingRelations: null == outgoingRelations
                ? _value.outgoingRelations
                : outgoingRelations // ignore: cast_nullable_to_non_nullable
                      as List<IssueRelationModel>,
            incomingRelation: freezed == incomingRelation
                ? _value.incomingRelation
                : incomingRelation // ignore: cast_nullable_to_non_nullable
                      as IssueRelationModel?,
            creator: freezed == creator
                ? _value.creator
                : creator // ignore: cast_nullable_to_non_nullable
                      as SimpleUserModel?,
            updater: freezed == updater
                ? _value.updater
                : updater // ignore: cast_nullable_to_non_nullable
                      as int?,
            created: null == created
                ? _value.created
                : created // ignore: cast_nullable_to_non_nullable
                      as String,
            updated: null == updated
                ? _value.updated
                : updated // ignore: cast_nullable_to_non_nullable
                      as String,
          )
          as $Val,
    );
  }

  /// Create a copy of IssueModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SimpleProjectModelCopyWith<$Res> get project {
    return $SimpleProjectModelCopyWith<$Res>(_value.project, (value) {
      return _then(_value.copyWith(project: value) as $Val);
    });
  }

  /// Create a copy of IssueModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $IssueTrackerModelCopyWith<$Res> get tracker {
    return $IssueTrackerModelCopyWith<$Res>(_value.tracker, (value) {
      return _then(_value.copyWith(tracker: value) as $Val);
    });
  }

  /// Create a copy of IssueModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $IssueStatusModelCopyWith<$Res> get status {
    return $IssueStatusModelCopyWith<$Res>(_value.status, (value) {
      return _then(_value.copyWith(status: value) as $Val);
    });
  }

  /// Create a copy of IssueModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $IssuePriorityModelCopyWith<$Res> get priority {
    return $IssuePriorityModelCopyWith<$Res>(_value.priority, (value) {
      return _then(_value.copyWith(priority: value) as $Val);
    });
  }

  /// Create a copy of IssueModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $IssueVersionModelCopyWith<$Res>? get fixedVersion {
    if (_value.fixedVersion == null) {
      return null;
    }

    return $IssueVersionModelCopyWith<$Res>(_value.fixedVersion!, (value) {
      return _then(_value.copyWith(fixedVersion: value) as $Val);
    });
  }

  /// Create a copy of IssueModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SimpleUserModelCopyWith<$Res>? get assignedTo {
    if (_value.assignedTo == null) {
      return null;
    }

    return $SimpleUserModelCopyWith<$Res>(_value.assignedTo!, (value) {
      return _then(_value.copyWith(assignedTo: value) as $Val);
    });
  }

  /// Create a copy of IssueModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $ParentIssueModelCopyWith<$Res>? get parent {
    if (_value.parent == null) {
      return null;
    }

    return $ParentIssueModelCopyWith<$Res>(_value.parent!, (value) {
      return _then(_value.copyWith(parent: value) as $Val);
    });
  }

  /// Create a copy of IssueModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $MeetingDescModelCopyWith<$Res>? get meetingDesc {
    if (_value.meetingDesc == null) {
      return null;
    }

    return $MeetingDescModelCopyWith<$Res>(_value.meetingDesc!, (value) {
      return _then(_value.copyWith(meetingDesc: value) as $Val);
    });
  }

  /// Create a copy of IssueModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $IssueRelationModelCopyWith<$Res>? get incomingRelation {
    if (_value.incomingRelation == null) {
      return null;
    }

    return $IssueRelationModelCopyWith<$Res>(_value.incomingRelation!, (value) {
      return _then(_value.copyWith(incomingRelation: value) as $Val);
    });
  }

  /// Create a copy of IssueModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SimpleUserModelCopyWith<$Res>? get creator {
    if (_value.creator == null) {
      return null;
    }

    return $SimpleUserModelCopyWith<$Res>(_value.creator!, (value) {
      return _then(_value.copyWith(creator: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$IssueModelImplCopyWith<$Res>
    implements $IssueModelCopyWith<$Res> {
  factory _$$IssueModelImplCopyWith(
    _$IssueModelImpl value,
    $Res Function(_$IssueModelImpl) then,
  ) = __$$IssueModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int pk,
    SimpleProjectModel project,
    IssueTrackerModel tracker,
    IssueStatusModel status,
    IssuePriorityModel priority,
    String subject,
    String description,
    int? category,
    IssueVersionModel? fixedVersion,
    SimpleUserModel? assignedTo,
    ParentIssueModel? parent,
    List<SimpleUserModel> watchers,
    bool isPrivate,
    String? expectedDuration,
    String expectedDurationDisplay,
    String startDate,
    String? dueDate,
    int? meeting,
    MeetingDescModel? meetingDesc,
    int doneRatio,
    String? closed,
    List<IssueFileModel> files,
    List<IssueLinkModel> links,
    List<SubIssueModel> subIssues,
    List<IssueRelationModel> outgoingRelations,
    IssueRelationModel? incomingRelation,
    SimpleUserModel? creator,
    int? updater,
    String created,
    String updated,
  });

  @override
  $SimpleProjectModelCopyWith<$Res> get project;
  @override
  $IssueTrackerModelCopyWith<$Res> get tracker;
  @override
  $IssueStatusModelCopyWith<$Res> get status;
  @override
  $IssuePriorityModelCopyWith<$Res> get priority;
  @override
  $IssueVersionModelCopyWith<$Res>? get fixedVersion;
  @override
  $SimpleUserModelCopyWith<$Res>? get assignedTo;
  @override
  $ParentIssueModelCopyWith<$Res>? get parent;
  @override
  $MeetingDescModelCopyWith<$Res>? get meetingDesc;
  @override
  $IssueRelationModelCopyWith<$Res>? get incomingRelation;
  @override
  $SimpleUserModelCopyWith<$Res>? get creator;
}

/// @nodoc
class __$$IssueModelImplCopyWithImpl<$Res>
    extends _$IssueModelCopyWithImpl<$Res, _$IssueModelImpl>
    implements _$$IssueModelImplCopyWith<$Res> {
  __$$IssueModelImplCopyWithImpl(
    _$IssueModelImpl _value,
    $Res Function(_$IssueModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of IssueModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? project = null,
    Object? tracker = null,
    Object? status = null,
    Object? priority = null,
    Object? subject = null,
    Object? description = null,
    Object? category = freezed,
    Object? fixedVersion = freezed,
    Object? assignedTo = freezed,
    Object? parent = freezed,
    Object? watchers = null,
    Object? isPrivate = null,
    Object? expectedDuration = freezed,
    Object? expectedDurationDisplay = null,
    Object? startDate = null,
    Object? dueDate = freezed,
    Object? meeting = freezed,
    Object? meetingDesc = freezed,
    Object? doneRatio = null,
    Object? closed = freezed,
    Object? files = null,
    Object? links = null,
    Object? subIssues = null,
    Object? outgoingRelations = null,
    Object? incomingRelation = freezed,
    Object? creator = freezed,
    Object? updater = freezed,
    Object? created = null,
    Object? updated = null,
  }) {
    return _then(
      _$IssueModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        project: null == project
            ? _value.project
            : project // ignore: cast_nullable_to_non_nullable
                  as SimpleProjectModel,
        tracker: null == tracker
            ? _value.tracker
            : tracker // ignore: cast_nullable_to_non_nullable
                  as IssueTrackerModel,
        status: null == status
            ? _value.status
            : status // ignore: cast_nullable_to_non_nullable
                  as IssueStatusModel,
        priority: null == priority
            ? _value.priority
            : priority // ignore: cast_nullable_to_non_nullable
                  as IssuePriorityModel,
        subject: null == subject
            ? _value.subject
            : subject // ignore: cast_nullable_to_non_nullable
                  as String,
        description: null == description
            ? _value.description
            : description // ignore: cast_nullable_to_non_nullable
                  as String,
        category: freezed == category
            ? _value.category
            : category // ignore: cast_nullable_to_non_nullable
                  as int?,
        fixedVersion: freezed == fixedVersion
            ? _value.fixedVersion
            : fixedVersion // ignore: cast_nullable_to_non_nullable
                  as IssueVersionModel?,
        assignedTo: freezed == assignedTo
            ? _value.assignedTo
            : assignedTo // ignore: cast_nullable_to_non_nullable
                  as SimpleUserModel?,
        parent: freezed == parent
            ? _value.parent
            : parent // ignore: cast_nullable_to_non_nullable
                  as ParentIssueModel?,
        watchers: null == watchers
            ? _value._watchers
            : watchers // ignore: cast_nullable_to_non_nullable
                  as List<SimpleUserModel>,
        isPrivate: null == isPrivate
            ? _value.isPrivate
            : isPrivate // ignore: cast_nullable_to_non_nullable
                  as bool,
        expectedDuration: freezed == expectedDuration
            ? _value.expectedDuration
            : expectedDuration // ignore: cast_nullable_to_non_nullable
                  as String?,
        expectedDurationDisplay: null == expectedDurationDisplay
            ? _value.expectedDurationDisplay
            : expectedDurationDisplay // ignore: cast_nullable_to_non_nullable
                  as String,
        startDate: null == startDate
            ? _value.startDate
            : startDate // ignore: cast_nullable_to_non_nullable
                  as String,
        dueDate: freezed == dueDate
            ? _value.dueDate
            : dueDate // ignore: cast_nullable_to_non_nullable
                  as String?,
        meeting: freezed == meeting
            ? _value.meeting
            : meeting // ignore: cast_nullable_to_non_nullable
                  as int?,
        meetingDesc: freezed == meetingDesc
            ? _value.meetingDesc
            : meetingDesc // ignore: cast_nullable_to_non_nullable
                  as MeetingDescModel?,
        doneRatio: null == doneRatio
            ? _value.doneRatio
            : doneRatio // ignore: cast_nullable_to_non_nullable
                  as int,
        closed: freezed == closed
            ? _value.closed
            : closed // ignore: cast_nullable_to_non_nullable
                  as String?,
        files: null == files
            ? _value._files
            : files // ignore: cast_nullable_to_non_nullable
                  as List<IssueFileModel>,
        links: null == links
            ? _value._links
            : links // ignore: cast_nullable_to_non_nullable
                  as List<IssueLinkModel>,
        subIssues: null == subIssues
            ? _value._subIssues
            : subIssues // ignore: cast_nullable_to_non_nullable
                  as List<SubIssueModel>,
        outgoingRelations: null == outgoingRelations
            ? _value._outgoingRelations
            : outgoingRelations // ignore: cast_nullable_to_non_nullable
                  as List<IssueRelationModel>,
        incomingRelation: freezed == incomingRelation
            ? _value.incomingRelation
            : incomingRelation // ignore: cast_nullable_to_non_nullable
                  as IssueRelationModel?,
        creator: freezed == creator
            ? _value.creator
            : creator // ignore: cast_nullable_to_non_nullable
                  as SimpleUserModel?,
        updater: freezed == updater
            ? _value.updater
            : updater // ignore: cast_nullable_to_non_nullable
                  as int?,
        created: null == created
            ? _value.created
            : created // ignore: cast_nullable_to_non_nullable
                  as String,
        updated: null == updated
            ? _value.updated
            : updated // ignore: cast_nullable_to_non_nullable
                  as String,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$IssueModelImpl implements _IssueModel {
  const _$IssueModelImpl({
    required this.pk,
    required this.project,
    required this.tracker,
    required this.status,
    required this.priority,
    required this.subject,
    this.description = '',
    this.category,
    this.fixedVersion,
    this.assignedTo,
    this.parent,
    final List<SimpleUserModel> watchers = const [],
    this.isPrivate = false,
    this.expectedDuration,
    this.expectedDurationDisplay = '',
    required this.startDate,
    this.dueDate,
    this.meeting,
    this.meetingDesc,
    this.doneRatio = 0,
    this.closed,
    final List<IssueFileModel> files = const [],
    final List<IssueLinkModel> links = const [],
    final List<SubIssueModel> subIssues = const [],
    final List<IssueRelationModel> outgoingRelations = const [],
    this.incomingRelation,
    this.creator,
    this.updater,
    required this.created,
    required this.updated,
  }) : _watchers = watchers,
       _files = files,
       _links = links,
       _subIssues = subIssues,
       _outgoingRelations = outgoingRelations;

  factory _$IssueModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$IssueModelImplFromJson(json);

  @override
  final int pk;
  @override
  final SimpleProjectModel project;
  @override
  final IssueTrackerModel tracker;
  @override
  final IssueStatusModel status;
  @override
  final IssuePriorityModel priority;
  @override
  final String subject;
  @override
  @JsonKey()
  final String description;
  @override
  final int? category;
  @override
  final IssueVersionModel? fixedVersion;
  @override
  final SimpleUserModel? assignedTo;
  @override
  final ParentIssueModel? parent;
  final List<SimpleUserModel> _watchers;
  @override
  @JsonKey()
  List<SimpleUserModel> get watchers {
    if (_watchers is EqualUnmodifiableListView) return _watchers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_watchers);
  }

  @override
  @JsonKey()
  final bool isPrivate;
  @override
  final String? expectedDuration;
  @override
  @JsonKey()
  final String expectedDurationDisplay;
  @override
  final String startDate;
  @override
  final String? dueDate;
  @override
  final int? meeting;
  @override
  final MeetingDescModel? meetingDesc;
  @override
  @JsonKey()
  final int doneRatio;
  @override
  final String? closed;
  final List<IssueFileModel> _files;
  @override
  @JsonKey()
  List<IssueFileModel> get files {
    if (_files is EqualUnmodifiableListView) return _files;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_files);
  }

  final List<IssueLinkModel> _links;
  @override
  @JsonKey()
  List<IssueLinkModel> get links {
    if (_links is EqualUnmodifiableListView) return _links;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_links);
  }

  final List<SubIssueModel> _subIssues;
  @override
  @JsonKey()
  List<SubIssueModel> get subIssues {
    if (_subIssues is EqualUnmodifiableListView) return _subIssues;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_subIssues);
  }

  final List<IssueRelationModel> _outgoingRelations;
  @override
  @JsonKey()
  List<IssueRelationModel> get outgoingRelations {
    if (_outgoingRelations is EqualUnmodifiableListView)
      return _outgoingRelations;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_outgoingRelations);
  }

  @override
  final IssueRelationModel? incomingRelation;
  @override
  final SimpleUserModel? creator;
  @override
  final int? updater;
  @override
  final String created;
  @override
  final String updated;

  @override
  String toString() {
    return 'IssueModel(pk: $pk, project: $project, tracker: $tracker, status: $status, priority: $priority, subject: $subject, description: $description, category: $category, fixedVersion: $fixedVersion, assignedTo: $assignedTo, parent: $parent, watchers: $watchers, isPrivate: $isPrivate, expectedDuration: $expectedDuration, expectedDurationDisplay: $expectedDurationDisplay, startDate: $startDate, dueDate: $dueDate, meeting: $meeting, meetingDesc: $meetingDesc, doneRatio: $doneRatio, closed: $closed, files: $files, links: $links, subIssues: $subIssues, outgoingRelations: $outgoingRelations, incomingRelation: $incomingRelation, creator: $creator, updater: $updater, created: $created, updated: $updated)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$IssueModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.project, project) || other.project == project) &&
            (identical(other.tracker, tracker) || other.tracker == tracker) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.priority, priority) ||
                other.priority == priority) &&
            (identical(other.subject, subject) || other.subject == subject) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.category, category) ||
                other.category == category) &&
            (identical(other.fixedVersion, fixedVersion) ||
                other.fixedVersion == fixedVersion) &&
            (identical(other.assignedTo, assignedTo) ||
                other.assignedTo == assignedTo) &&
            (identical(other.parent, parent) || other.parent == parent) &&
            const DeepCollectionEquality().equals(other._watchers, _watchers) &&
            (identical(other.isPrivate, isPrivate) ||
                other.isPrivate == isPrivate) &&
            (identical(other.expectedDuration, expectedDuration) ||
                other.expectedDuration == expectedDuration) &&
            (identical(
                  other.expectedDurationDisplay,
                  expectedDurationDisplay,
                ) ||
                other.expectedDurationDisplay == expectedDurationDisplay) &&
            (identical(other.startDate, startDate) ||
                other.startDate == startDate) &&
            (identical(other.dueDate, dueDate) || other.dueDate == dueDate) &&
            (identical(other.meeting, meeting) || other.meeting == meeting) &&
            (identical(other.meetingDesc, meetingDesc) ||
                other.meetingDesc == meetingDesc) &&
            (identical(other.doneRatio, doneRatio) ||
                other.doneRatio == doneRatio) &&
            (identical(other.closed, closed) || other.closed == closed) &&
            const DeepCollectionEquality().equals(other._files, _files) &&
            const DeepCollectionEquality().equals(other._links, _links) &&
            const DeepCollectionEquality().equals(
              other._subIssues,
              _subIssues,
            ) &&
            const DeepCollectionEquality().equals(
              other._outgoingRelations,
              _outgoingRelations,
            ) &&
            (identical(other.incomingRelation, incomingRelation) ||
                other.incomingRelation == incomingRelation) &&
            (identical(other.creator, creator) || other.creator == creator) &&
            (identical(other.updater, updater) || other.updater == updater) &&
            (identical(other.created, created) || other.created == created) &&
            (identical(other.updated, updated) || other.updated == updated));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hashAll([
    runtimeType,
    pk,
    project,
    tracker,
    status,
    priority,
    subject,
    description,
    category,
    fixedVersion,
    assignedTo,
    parent,
    const DeepCollectionEquality().hash(_watchers),
    isPrivate,
    expectedDuration,
    expectedDurationDisplay,
    startDate,
    dueDate,
    meeting,
    meetingDesc,
    doneRatio,
    closed,
    const DeepCollectionEquality().hash(_files),
    const DeepCollectionEquality().hash(_links),
    const DeepCollectionEquality().hash(_subIssues),
    const DeepCollectionEquality().hash(_outgoingRelations),
    incomingRelation,
    creator,
    updater,
    created,
    updated,
  ]);

  /// Create a copy of IssueModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$IssueModelImplCopyWith<_$IssueModelImpl> get copyWith =>
      __$$IssueModelImplCopyWithImpl<_$IssueModelImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$IssueModelImplToJson(this);
  }
}

abstract class _IssueModel implements IssueModel {
  const factory _IssueModel({
    required final int pk,
    required final SimpleProjectModel project,
    required final IssueTrackerModel tracker,
    required final IssueStatusModel status,
    required final IssuePriorityModel priority,
    required final String subject,
    final String description,
    final int? category,
    final IssueVersionModel? fixedVersion,
    final SimpleUserModel? assignedTo,
    final ParentIssueModel? parent,
    final List<SimpleUserModel> watchers,
    final bool isPrivate,
    final String? expectedDuration,
    final String expectedDurationDisplay,
    required final String startDate,
    final String? dueDate,
    final int? meeting,
    final MeetingDescModel? meetingDesc,
    final int doneRatio,
    final String? closed,
    final List<IssueFileModel> files,
    final List<IssueLinkModel> links,
    final List<SubIssueModel> subIssues,
    final List<IssueRelationModel> outgoingRelations,
    final IssueRelationModel? incomingRelation,
    final SimpleUserModel? creator,
    final int? updater,
    required final String created,
    required final String updated,
  }) = _$IssueModelImpl;

  factory _IssueModel.fromJson(Map<String, dynamic> json) =
      _$IssueModelImpl.fromJson;

  @override
  int get pk;
  @override
  SimpleProjectModel get project;
  @override
  IssueTrackerModel get tracker;
  @override
  IssueStatusModel get status;
  @override
  IssuePriorityModel get priority;
  @override
  String get subject;
  @override
  String get description;
  @override
  int? get category;
  @override
  IssueVersionModel? get fixedVersion;
  @override
  SimpleUserModel? get assignedTo;
  @override
  ParentIssueModel? get parent;
  @override
  List<SimpleUserModel> get watchers;
  @override
  bool get isPrivate;
  @override
  String? get expectedDuration;
  @override
  String get expectedDurationDisplay;
  @override
  String get startDate;
  @override
  String? get dueDate;
  @override
  int? get meeting;
  @override
  MeetingDescModel? get meetingDesc;
  @override
  int get doneRatio;
  @override
  String? get closed;
  @override
  List<IssueFileModel> get files;
  @override
  List<IssueLinkModel> get links;
  @override
  List<SubIssueModel> get subIssues;
  @override
  List<IssueRelationModel> get outgoingRelations;
  @override
  IssueRelationModel? get incomingRelation;
  @override
  SimpleUserModel? get creator;
  @override
  int? get updater;
  @override
  String get created;
  @override
  String get updated;

  /// Create a copy of IssueModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$IssueModelImplCopyWith<_$IssueModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

IssueListResponse _$IssueListResponseFromJson(Map<String, dynamic> json) {
  return _IssueListResponse.fromJson(json);
}

/// @nodoc
mixin _$IssueListResponse {
  int get count => throw _privateConstructorUsedError;
  String? get next => throw _privateConstructorUsedError;
  String? get previous => throw _privateConstructorUsedError;
  List<IssueModel> get results => throw _privateConstructorUsedError;

  /// Serializes this IssueListResponse to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of IssueListResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $IssueListResponseCopyWith<IssueListResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $IssueListResponseCopyWith<$Res> {
  factory $IssueListResponseCopyWith(
    IssueListResponse value,
    $Res Function(IssueListResponse) then,
  ) = _$IssueListResponseCopyWithImpl<$Res, IssueListResponse>;
  @useResult
  $Res call({
    int count,
    String? next,
    String? previous,
    List<IssueModel> results,
  });
}

/// @nodoc
class _$IssueListResponseCopyWithImpl<$Res, $Val extends IssueListResponse>
    implements $IssueListResponseCopyWith<$Res> {
  _$IssueListResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of IssueListResponse
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? count = null,
    Object? next = freezed,
    Object? previous = freezed,
    Object? results = null,
  }) {
    return _then(
      _value.copyWith(
            count: null == count
                ? _value.count
                : count // ignore: cast_nullable_to_non_nullable
                      as int,
            next: freezed == next
                ? _value.next
                : next // ignore: cast_nullable_to_non_nullable
                      as String?,
            previous: freezed == previous
                ? _value.previous
                : previous // ignore: cast_nullable_to_non_nullable
                      as String?,
            results: null == results
                ? _value.results
                : results // ignore: cast_nullable_to_non_nullable
                      as List<IssueModel>,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$IssueListResponseImplCopyWith<$Res>
    implements $IssueListResponseCopyWith<$Res> {
  factory _$$IssueListResponseImplCopyWith(
    _$IssueListResponseImpl value,
    $Res Function(_$IssueListResponseImpl) then,
  ) = __$$IssueListResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int count,
    String? next,
    String? previous,
    List<IssueModel> results,
  });
}

/// @nodoc
class __$$IssueListResponseImplCopyWithImpl<$Res>
    extends _$IssueListResponseCopyWithImpl<$Res, _$IssueListResponseImpl>
    implements _$$IssueListResponseImplCopyWith<$Res> {
  __$$IssueListResponseImplCopyWithImpl(
    _$IssueListResponseImpl _value,
    $Res Function(_$IssueListResponseImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of IssueListResponse
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? count = null,
    Object? next = freezed,
    Object? previous = freezed,
    Object? results = null,
  }) {
    return _then(
      _$IssueListResponseImpl(
        count: null == count
            ? _value.count
            : count // ignore: cast_nullable_to_non_nullable
                  as int,
        next: freezed == next
            ? _value.next
            : next // ignore: cast_nullable_to_non_nullable
                  as String?,
        previous: freezed == previous
            ? _value.previous
            : previous // ignore: cast_nullable_to_non_nullable
                  as String?,
        results: null == results
            ? _value._results
            : results // ignore: cast_nullable_to_non_nullable
                  as List<IssueModel>,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$IssueListResponseImpl implements _IssueListResponse {
  const _$IssueListResponseImpl({
    required this.count,
    this.next,
    this.previous,
    required final List<IssueModel> results,
  }) : _results = results;

  factory _$IssueListResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$IssueListResponseImplFromJson(json);

  @override
  final int count;
  @override
  final String? next;
  @override
  final String? previous;
  final List<IssueModel> _results;
  @override
  List<IssueModel> get results {
    if (_results is EqualUnmodifiableListView) return _results;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_results);
  }

  @override
  String toString() {
    return 'IssueListResponse(count: $count, next: $next, previous: $previous, results: $results)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$IssueListResponseImpl &&
            (identical(other.count, count) || other.count == count) &&
            (identical(other.next, next) || other.next == next) &&
            (identical(other.previous, previous) ||
                other.previous == previous) &&
            const DeepCollectionEquality().equals(other._results, _results));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
    runtimeType,
    count,
    next,
    previous,
    const DeepCollectionEquality().hash(_results),
  );

  /// Create a copy of IssueListResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$IssueListResponseImplCopyWith<_$IssueListResponseImpl> get copyWith =>
      __$$IssueListResponseImplCopyWithImpl<_$IssueListResponseImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$IssueListResponseImplToJson(this);
  }
}

abstract class _IssueListResponse implements IssueListResponse {
  const factory _IssueListResponse({
    required final int count,
    final String? next,
    final String? previous,
    required final List<IssueModel> results,
  }) = _$IssueListResponseImpl;

  factory _IssueListResponse.fromJson(Map<String, dynamic> json) =
      _$IssueListResponseImpl.fromJson;

  @override
  int get count;
  @override
  String? get next;
  @override
  String? get previous;
  @override
  List<IssueModel> get results;

  /// Create a copy of IssueListResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$IssueListResponseImplCopyWith<_$IssueListResponseImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
