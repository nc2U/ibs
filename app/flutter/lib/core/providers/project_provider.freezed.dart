// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'project_provider.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
  'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models',
);

/// @nodoc
mixin _$SelectedProject {
  int get pk => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  String get slug => throw _privateConstructorUsedError;
  String? get description => throw _privateConstructorUsedError;
  String get type => throw _privateConstructorUsedError;
  bool get isPublic => throw _privateConstructorUsedError;

  /// Create a copy of SelectedProject
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $SelectedProjectCopyWith<SelectedProject> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $SelectedProjectCopyWith<$Res> {
  factory $SelectedProjectCopyWith(
    SelectedProject value,
    $Res Function(SelectedProject) then,
  ) = _$SelectedProjectCopyWithImpl<$Res, SelectedProject>;
  @useResult
  $Res call({
    int pk,
    String name,
    String slug,
    String? description,
    String type,
    bool isPublic,
  });
}

/// @nodoc
class _$SelectedProjectCopyWithImpl<$Res, $Val extends SelectedProject>
    implements $SelectedProjectCopyWith<$Res> {
  _$SelectedProjectCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of SelectedProject
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? name = null,
    Object? slug = null,
    Object? description = freezed,
    Object? type = null,
    Object? isPublic = null,
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
            description: freezed == description
                ? _value.description
                : description // ignore: cast_nullable_to_non_nullable
                      as String?,
            type: null == type
                ? _value.type
                : type // ignore: cast_nullable_to_non_nullable
                      as String,
            isPublic: null == isPublic
                ? _value.isPublic
                : isPublic // ignore: cast_nullable_to_non_nullable
                      as bool,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$SelectedProjectImplCopyWith<$Res>
    implements $SelectedProjectCopyWith<$Res> {
  factory _$$SelectedProjectImplCopyWith(
    _$SelectedProjectImpl value,
    $Res Function(_$SelectedProjectImpl) then,
  ) = __$$SelectedProjectImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int pk,
    String name,
    String slug,
    String? description,
    String type,
    bool isPublic,
  });
}

/// @nodoc
class __$$SelectedProjectImplCopyWithImpl<$Res>
    extends _$SelectedProjectCopyWithImpl<$Res, _$SelectedProjectImpl>
    implements _$$SelectedProjectImplCopyWith<$Res> {
  __$$SelectedProjectImplCopyWithImpl(
    _$SelectedProjectImpl _value,
    $Res Function(_$SelectedProjectImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of SelectedProject
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? name = null,
    Object? slug = null,
    Object? description = freezed,
    Object? type = null,
    Object? isPublic = null,
  }) {
    return _then(
      _$SelectedProjectImpl(
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
        description: freezed == description
            ? _value.description
            : description // ignore: cast_nullable_to_non_nullable
                  as String?,
        type: null == type
            ? _value.type
            : type // ignore: cast_nullable_to_non_nullable
                  as String,
        isPublic: null == isPublic
            ? _value.isPublic
            : isPublic // ignore: cast_nullable_to_non_nullable
                  as bool,
      ),
    );
  }
}

/// @nodoc

class _$SelectedProjectImpl implements _SelectedProject {
  const _$SelectedProjectImpl({
    required this.pk,
    required this.name,
    required this.slug,
    this.description,
    this.type = '1',
    this.isPublic = false,
  });

  @override
  final int pk;
  @override
  final String name;
  @override
  final String slug;
  @override
  final String? description;
  @override
  @JsonKey()
  final String type;
  @override
  @JsonKey()
  final bool isPublic;

  @override
  String toString() {
    return 'SelectedProject(pk: $pk, name: $name, slug: $slug, description: $description, type: $type, isPublic: $isPublic)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SelectedProjectImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.slug, slug) || other.slug == slug) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.isPublic, isPublic) ||
                other.isPublic == isPublic));
  }

  @override
  int get hashCode =>
      Object.hash(runtimeType, pk, name, slug, description, type, isPublic);

  /// Create a copy of SelectedProject
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$SelectedProjectImplCopyWith<_$SelectedProjectImpl> get copyWith =>
      __$$SelectedProjectImplCopyWithImpl<_$SelectedProjectImpl>(
        this,
        _$identity,
      );
}

abstract class _SelectedProject implements SelectedProject {
  const factory _SelectedProject({
    required final int pk,
    required final String name,
    required final String slug,
    final String? description,
    final String type,
    final bool isPublic,
  }) = _$SelectedProjectImpl;

  @override
  int get pk;
  @override
  String get name;
  @override
  String get slug;
  @override
  String? get description;
  @override
  String get type;
  @override
  bool get isPublic;

  /// Create a copy of SelectedProject
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$SelectedProjectImplCopyWith<_$SelectedProjectImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
