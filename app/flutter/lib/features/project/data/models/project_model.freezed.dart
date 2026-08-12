// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'project_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
  'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models',
);

ProjectModel _$ProjectModelFromJson(Map<String, dynamic> json) {
  return _ProjectModel.fromJson(json);
}

/// @nodoc
mixin _$ProjectModel {
  int get pk => throw _privateConstructorUsedError;
  @JsonKey(fromJson: _parseString)
  String get name => throw _privateConstructorUsedError;
  @JsonKey(fromJson: _parseString)
  String get slug => throw _privateConstructorUsedError;
  @JsonKey(fromJson: _parseString)
  String get description => throw _privateConstructorUsedError;
  @JsonKey(fromJson: _parseType)
  String get type => throw _privateConstructorUsedError;
  @JsonKey(fromJson: _parseType)
  String get status => throw _privateConstructorUsedError;
  bool get visible => throw _privateConstructorUsedError;
  bool get isBookmarked => throw _privateConstructorUsedError;

  /// Serializes this ProjectModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ProjectModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ProjectModelCopyWith<ProjectModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ProjectModelCopyWith<$Res> {
  factory $ProjectModelCopyWith(
    ProjectModel value,
    $Res Function(ProjectModel) then,
  ) = _$ProjectModelCopyWithImpl<$Res, ProjectModel>;
  @useResult
  $Res call({
    int pk,
    @JsonKey(fromJson: _parseString) String name,
    @JsonKey(fromJson: _parseString) String slug,
    @JsonKey(fromJson: _parseString) String description,
    @JsonKey(fromJson: _parseType) String type,
    @JsonKey(fromJson: _parseType) String status,
    bool visible,
    bool isBookmarked,
  });
}

/// @nodoc
class _$ProjectModelCopyWithImpl<$Res, $Val extends ProjectModel>
    implements $ProjectModelCopyWith<$Res> {
  _$ProjectModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ProjectModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? name = null,
    Object? slug = null,
    Object? description = null,
    Object? type = null,
    Object? status = null,
    Object? visible = null,
    Object? isBookmarked = null,
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
            slug: null == slug
                ? _value.slug
                : slug // ignore: cast_nullable_to_non_nullable
                      as String,
            description: null == description
                ? _value.description
                : description // ignore: cast_nullable_to_non_nullable
                      as String,
            type: null == type
                ? _value.type
                : type // ignore: cast_nullable_to_non_nullable
                      as String,
            status: null == status
                ? _value.status
                : status // ignore: cast_nullable_to_non_nullable
                      as String,
            visible: null == visible
                ? _value.visible
                : visible // ignore: cast_nullable_to_non_nullable
                      as bool,
            isBookmarked: null == isBookmarked
                ? _value.isBookmarked
                : isBookmarked // ignore: cast_nullable_to_non_nullable
                      as bool,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$ProjectModelImplCopyWith<$Res>
    implements $ProjectModelCopyWith<$Res> {
  factory _$$ProjectModelImplCopyWith(
    _$ProjectModelImpl value,
    $Res Function(_$ProjectModelImpl) then,
  ) = __$$ProjectModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int pk,
    @JsonKey(fromJson: _parseString) String name,
    @JsonKey(fromJson: _parseString) String slug,
    @JsonKey(fromJson: _parseString) String description,
    @JsonKey(fromJson: _parseType) String type,
    @JsonKey(fromJson: _parseType) String status,
    bool visible,
    bool isBookmarked,
  });
}

/// @nodoc
class __$$ProjectModelImplCopyWithImpl<$Res>
    extends _$ProjectModelCopyWithImpl<$Res, _$ProjectModelImpl>
    implements _$$ProjectModelImplCopyWith<$Res> {
  __$$ProjectModelImplCopyWithImpl(
    _$ProjectModelImpl _value,
    $Res Function(_$ProjectModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of ProjectModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? name = null,
    Object? slug = null,
    Object? description = null,
    Object? type = null,
    Object? status = null,
    Object? visible = null,
    Object? isBookmarked = null,
  }) {
    return _then(
      _$ProjectModelImpl(
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
        description: null == description
            ? _value.description
            : description // ignore: cast_nullable_to_non_nullable
                  as String,
        type: null == type
            ? _value.type
            : type // ignore: cast_nullable_to_non_nullable
                  as String,
        status: null == status
            ? _value.status
            : status // ignore: cast_nullable_to_non_nullable
                  as String,
        visible: null == visible
            ? _value.visible
            : visible // ignore: cast_nullable_to_non_nullable
                  as bool,
        isBookmarked: null == isBookmarked
            ? _value.isBookmarked
            : isBookmarked // ignore: cast_nullable_to_non_nullable
                  as bool,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$ProjectModelImpl implements _ProjectModel {
  const _$ProjectModelImpl({
    required this.pk,
    @JsonKey(fromJson: _parseString) this.name = '',
    @JsonKey(fromJson: _parseString) this.slug = '',
    @JsonKey(fromJson: _parseString) this.description = '',
    @JsonKey(fromJson: _parseType) this.type = '1',
    @JsonKey(fromJson: _parseType) this.status = '1',
    this.visible = true,
    this.isBookmarked = false,
  });

  factory _$ProjectModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$ProjectModelImplFromJson(json);

  @override
  final int pk;
  @override
  @JsonKey(fromJson: _parseString)
  final String name;
  @override
  @JsonKey(fromJson: _parseString)
  final String slug;
  @override
  @JsonKey(fromJson: _parseString)
  final String description;
  @override
  @JsonKey(fromJson: _parseType)
  final String type;
  @override
  @JsonKey(fromJson: _parseType)
  final String status;
  @override
  @JsonKey()
  final bool visible;
  @override
  @JsonKey()
  final bool isBookmarked;

  @override
  String toString() {
    return 'ProjectModel(pk: $pk, name: $name, slug: $slug, description: $description, type: $type, status: $status, visible: $visible, isBookmarked: $isBookmarked)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ProjectModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.slug, slug) || other.slug == slug) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.visible, visible) || other.visible == visible) &&
            (identical(other.isBookmarked, isBookmarked) ||
                other.isBookmarked == isBookmarked));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
    runtimeType,
    pk,
    name,
    slug,
    description,
    type,
    status,
    visible,
    isBookmarked,
  );

  /// Create a copy of ProjectModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ProjectModelImplCopyWith<_$ProjectModelImpl> get copyWith =>
      __$$ProjectModelImplCopyWithImpl<_$ProjectModelImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ProjectModelImplToJson(this);
  }
}

abstract class _ProjectModel implements ProjectModel {
  const factory _ProjectModel({
    required final int pk,
    @JsonKey(fromJson: _parseString) final String name,
    @JsonKey(fromJson: _parseString) final String slug,
    @JsonKey(fromJson: _parseString) final String description,
    @JsonKey(fromJson: _parseType) final String type,
    @JsonKey(fromJson: _parseType) final String status,
    final bool visible,
    final bool isBookmarked,
  }) = _$ProjectModelImpl;

  factory _ProjectModel.fromJson(Map<String, dynamic> json) =
      _$ProjectModelImpl.fromJson;

  @override
  int get pk;
  @override
  @JsonKey(fromJson: _parseString)
  String get name;
  @override
  @JsonKey(fromJson: _parseString)
  String get slug;
  @override
  @JsonKey(fromJson: _parseString)
  String get description;
  @override
  @JsonKey(fromJson: _parseType)
  String get type;
  @override
  @JsonKey(fromJson: _parseType)
  String get status;
  @override
  bool get visible;
  @override
  bool get isBookmarked;

  /// Create a copy of ProjectModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ProjectModelImplCopyWith<_$ProjectModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ProjectListResponse _$ProjectListResponseFromJson(Map<String, dynamic> json) {
  return _ProjectListResponse.fromJson(json);
}

/// @nodoc
mixin _$ProjectListResponse {
  int get count => throw _privateConstructorUsedError;
  String? get next => throw _privateConstructorUsedError;
  String? get previous => throw _privateConstructorUsedError;
  List<ProjectModel> get results => throw _privateConstructorUsedError;

  /// Serializes this ProjectListResponse to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ProjectListResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ProjectListResponseCopyWith<ProjectListResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ProjectListResponseCopyWith<$Res> {
  factory $ProjectListResponseCopyWith(
    ProjectListResponse value,
    $Res Function(ProjectListResponse) then,
  ) = _$ProjectListResponseCopyWithImpl<$Res, ProjectListResponse>;
  @useResult
  $Res call({
    int count,
    String? next,
    String? previous,
    List<ProjectModel> results,
  });
}

/// @nodoc
class _$ProjectListResponseCopyWithImpl<$Res, $Val extends ProjectListResponse>
    implements $ProjectListResponseCopyWith<$Res> {
  _$ProjectListResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ProjectListResponse
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
                      as List<ProjectModel>,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$ProjectListResponseImplCopyWith<$Res>
    implements $ProjectListResponseCopyWith<$Res> {
  factory _$$ProjectListResponseImplCopyWith(
    _$ProjectListResponseImpl value,
    $Res Function(_$ProjectListResponseImpl) then,
  ) = __$$ProjectListResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int count,
    String? next,
    String? previous,
    List<ProjectModel> results,
  });
}

/// @nodoc
class __$$ProjectListResponseImplCopyWithImpl<$Res>
    extends _$ProjectListResponseCopyWithImpl<$Res, _$ProjectListResponseImpl>
    implements _$$ProjectListResponseImplCopyWith<$Res> {
  __$$ProjectListResponseImplCopyWithImpl(
    _$ProjectListResponseImpl _value,
    $Res Function(_$ProjectListResponseImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of ProjectListResponse
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
      _$ProjectListResponseImpl(
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
                  as List<ProjectModel>,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$ProjectListResponseImpl implements _ProjectListResponse {
  const _$ProjectListResponseImpl({
    required this.count,
    this.next,
    this.previous,
    required final List<ProjectModel> results,
  }) : _results = results;

  factory _$ProjectListResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$ProjectListResponseImplFromJson(json);

  @override
  final int count;
  @override
  final String? next;
  @override
  final String? previous;
  final List<ProjectModel> _results;
  @override
  List<ProjectModel> get results {
    if (_results is EqualUnmodifiableListView) return _results;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_results);
  }

  @override
  String toString() {
    return 'ProjectListResponse(count: $count, next: $next, previous: $previous, results: $results)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ProjectListResponseImpl &&
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

  /// Create a copy of ProjectListResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ProjectListResponseImplCopyWith<_$ProjectListResponseImpl> get copyWith =>
      __$$ProjectListResponseImplCopyWithImpl<_$ProjectListResponseImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$ProjectListResponseImplToJson(this);
  }
}

abstract class _ProjectListResponse implements ProjectListResponse {
  const factory _ProjectListResponse({
    required final int count,
    final String? next,
    final String? previous,
    required final List<ProjectModel> results,
  }) = _$ProjectListResponseImpl;

  factory _ProjectListResponse.fromJson(Map<String, dynamic> json) =
      _$ProjectListResponseImpl.fromJson;

  @override
  int get count;
  @override
  String? get next;
  @override
  String? get previous;
  @override
  List<ProjectModel> get results;

  /// Create a copy of ProjectListResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ProjectListResponseImplCopyWith<_$ProjectListResponseImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
