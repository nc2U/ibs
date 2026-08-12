// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'meeting_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
  'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models',
);

MeetingCategoryModel _$MeetingCategoryModelFromJson(Map<String, dynamic> json) {
  return _MeetingCategoryModel.fromJson(json);
}

/// @nodoc
mixin _$MeetingCategoryModel {
  int get pk => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  String get color => throw _privateConstructorUsedError;
  int get order => throw _privateConstructorUsedError;

  /// Serializes this MeetingCategoryModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of MeetingCategoryModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $MeetingCategoryModelCopyWith<MeetingCategoryModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MeetingCategoryModelCopyWith<$Res> {
  factory $MeetingCategoryModelCopyWith(
    MeetingCategoryModel value,
    $Res Function(MeetingCategoryModel) then,
  ) = _$MeetingCategoryModelCopyWithImpl<$Res, MeetingCategoryModel>;
  @useResult
  $Res call({int pk, String name, String color, int order});
}

/// @nodoc
class _$MeetingCategoryModelCopyWithImpl<
  $Res,
  $Val extends MeetingCategoryModel
>
    implements $MeetingCategoryModelCopyWith<$Res> {
  _$MeetingCategoryModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of MeetingCategoryModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? name = null,
    Object? color = null,
    Object? order = null,
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
            color: null == color
                ? _value.color
                : color // ignore: cast_nullable_to_non_nullable
                      as String,
            order: null == order
                ? _value.order
                : order // ignore: cast_nullable_to_non_nullable
                      as int,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$MeetingCategoryModelImplCopyWith<$Res>
    implements $MeetingCategoryModelCopyWith<$Res> {
  factory _$$MeetingCategoryModelImplCopyWith(
    _$MeetingCategoryModelImpl value,
    $Res Function(_$MeetingCategoryModelImpl) then,
  ) = __$$MeetingCategoryModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({int pk, String name, String color, int order});
}

/// @nodoc
class __$$MeetingCategoryModelImplCopyWithImpl<$Res>
    extends _$MeetingCategoryModelCopyWithImpl<$Res, _$MeetingCategoryModelImpl>
    implements _$$MeetingCategoryModelImplCopyWith<$Res> {
  __$$MeetingCategoryModelImplCopyWithImpl(
    _$MeetingCategoryModelImpl _value,
    $Res Function(_$MeetingCategoryModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of MeetingCategoryModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? name = null,
    Object? color = null,
    Object? order = null,
  }) {
    return _then(
      _$MeetingCategoryModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        name: null == name
            ? _value.name
            : name // ignore: cast_nullable_to_non_nullable
                  as String,
        color: null == color
            ? _value.color
            : color // ignore: cast_nullable_to_non_nullable
                  as String,
        order: null == order
            ? _value.order
            : order // ignore: cast_nullable_to_non_nullable
                  as int,
      ),
    );
  }
}

/// @nodoc
@JsonSerializable()
class _$MeetingCategoryModelImpl implements _MeetingCategoryModel {
  const _$MeetingCategoryModelImpl({
    required this.pk,
    required this.name,
    this.color = '#6366F1',
    this.order = 0,
  });

  factory _$MeetingCategoryModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$MeetingCategoryModelImplFromJson(json);

  @override
  final int pk;
  @override
  final String name;
  @override
  @JsonKey()
  final String color;
  @override
  @JsonKey()
  final int order;

  @override
  String toString() {
    return 'MeetingCategoryModel(pk: $pk, name: $name, color: $color, order: $order)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MeetingCategoryModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.color, color) || other.color == color) &&
            (identical(other.order, order) || other.order == order));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, pk, name, color, order);

  /// Create a copy of MeetingCategoryModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$MeetingCategoryModelImplCopyWith<_$MeetingCategoryModelImpl>
  get copyWith =>
      __$$MeetingCategoryModelImplCopyWithImpl<_$MeetingCategoryModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$MeetingCategoryModelImplToJson(this);
  }
}

abstract class _MeetingCategoryModel implements MeetingCategoryModel {
  const factory _MeetingCategoryModel({
    required final int pk,
    required final String name,
    final String color,
    final int order,
  }) = _$MeetingCategoryModelImpl;

  factory _MeetingCategoryModel.fromJson(Map<String, dynamic> json) =
      _$MeetingCategoryModelImpl.fromJson;

  @override
  int get pk;
  @override
  String get name;
  @override
  String get color;
  @override
  int get order;

  /// Create a copy of MeetingCategoryModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$MeetingCategoryModelImplCopyWith<_$MeetingCategoryModelImpl>
  get copyWith => throw _privateConstructorUsedError;
}

MeetingFileModel _$MeetingFileModelFromJson(Map<String, dynamic> json) {
  return _MeetingFileModel.fromJson(json);
}

/// @nodoc
mixin _$MeetingFileModel {
  int get pk => throw _privateConstructorUsedError;
  String get file => throw _privateConstructorUsedError;
  String get fileName => throw _privateConstructorUsedError;
  String get fileType => throw _privateConstructorUsedError;
  int? get fileSize => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  String get created => throw _privateConstructorUsedError;
  SimpleUserModel? get creator => throw _privateConstructorUsedError;

  /// Serializes this MeetingFileModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of MeetingFileModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $MeetingFileModelCopyWith<MeetingFileModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MeetingFileModelCopyWith<$Res> {
  factory $MeetingFileModelCopyWith(
    MeetingFileModel value,
    $Res Function(MeetingFileModel) then,
  ) = _$MeetingFileModelCopyWithImpl<$Res, MeetingFileModel>;
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
class _$MeetingFileModelCopyWithImpl<$Res, $Val extends MeetingFileModel>
    implements $MeetingFileModelCopyWith<$Res> {
  _$MeetingFileModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of MeetingFileModel
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

  /// Create a copy of MeetingFileModel
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
abstract class _$$MeetingFileModelImplCopyWith<$Res>
    implements $MeetingFileModelCopyWith<$Res> {
  factory _$$MeetingFileModelImplCopyWith(
    _$MeetingFileModelImpl value,
    $Res Function(_$MeetingFileModelImpl) then,
  ) = __$$MeetingFileModelImplCopyWithImpl<$Res>;
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
class __$$MeetingFileModelImplCopyWithImpl<$Res>
    extends _$MeetingFileModelCopyWithImpl<$Res, _$MeetingFileModelImpl>
    implements _$$MeetingFileModelImplCopyWith<$Res> {
  __$$MeetingFileModelImplCopyWithImpl(
    _$MeetingFileModelImpl _value,
    $Res Function(_$MeetingFileModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of MeetingFileModel
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
      _$MeetingFileModelImpl(
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
@JsonSerializable()
class _$MeetingFileModelImpl implements _MeetingFileModel {
  const _$MeetingFileModelImpl({
    required this.pk,
    required this.file,
    required this.fileName,
    this.fileType = '',
    this.fileSize,
    this.description = '',
    required this.created,
    this.creator,
  });

  factory _$MeetingFileModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$MeetingFileModelImplFromJson(json);

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
    return 'MeetingFileModel(pk: $pk, file: $file, fileName: $fileName, fileType: $fileType, fileSize: $fileSize, description: $description, created: $created, creator: $creator)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MeetingFileModelImpl &&
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

  /// Create a copy of MeetingFileModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$MeetingFileModelImplCopyWith<_$MeetingFileModelImpl> get copyWith =>
      __$$MeetingFileModelImplCopyWithImpl<_$MeetingFileModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$MeetingFileModelImplToJson(this);
  }
}

abstract class _MeetingFileModel implements MeetingFileModel {
  const factory _MeetingFileModel({
    required final int pk,
    required final String file,
    required final String fileName,
    final String fileType,
    final int? fileSize,
    final String description,
    required final String created,
    final SimpleUserModel? creator,
  }) = _$MeetingFileModelImpl;

  factory _MeetingFileModel.fromJson(Map<String, dynamic> json) =
      _$MeetingFileModelImpl.fromJson;

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

  /// Create a copy of MeetingFileModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$MeetingFileModelImplCopyWith<_$MeetingFileModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

MeetingLinkModel _$MeetingLinkModelFromJson(Map<String, dynamic> json) {
  return _MeetingLinkModel.fromJson(json);
}

/// @nodoc
mixin _$MeetingLinkModel {
  int get pk => throw _privateConstructorUsedError;
  String get link => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  int get hit => throw _privateConstructorUsedError;
  String get created => throw _privateConstructorUsedError;
  SimpleUserModel? get creator => throw _privateConstructorUsedError;

  /// Serializes this MeetingLinkModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of MeetingLinkModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $MeetingLinkModelCopyWith<MeetingLinkModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MeetingLinkModelCopyWith<$Res> {
  factory $MeetingLinkModelCopyWith(
    MeetingLinkModel value,
    $Res Function(MeetingLinkModel) then,
  ) = _$MeetingLinkModelCopyWithImpl<$Res, MeetingLinkModel>;
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
class _$MeetingLinkModelCopyWithImpl<$Res, $Val extends MeetingLinkModel>
    implements $MeetingLinkModelCopyWith<$Res> {
  _$MeetingLinkModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of MeetingLinkModel
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

  /// Create a copy of MeetingLinkModel
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
abstract class _$$MeetingLinkModelImplCopyWith<$Res>
    implements $MeetingLinkModelCopyWith<$Res> {
  factory _$$MeetingLinkModelImplCopyWith(
    _$MeetingLinkModelImpl value,
    $Res Function(_$MeetingLinkModelImpl) then,
  ) = __$$MeetingLinkModelImplCopyWithImpl<$Res>;
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
class __$$MeetingLinkModelImplCopyWithImpl<$Res>
    extends _$MeetingLinkModelCopyWithImpl<$Res, _$MeetingLinkModelImpl>
    implements _$$MeetingLinkModelImplCopyWith<$Res> {
  __$$MeetingLinkModelImplCopyWithImpl(
    _$MeetingLinkModelImpl _value,
    $Res Function(_$MeetingLinkModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of MeetingLinkModel
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
      _$MeetingLinkModelImpl(
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
@JsonSerializable()
class _$MeetingLinkModelImpl implements _MeetingLinkModel {
  const _$MeetingLinkModelImpl({
    required this.pk,
    required this.link,
    required this.name,
    this.hit = 0,
    required this.created,
    this.creator,
  });

  factory _$MeetingLinkModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$MeetingLinkModelImplFromJson(json);

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
    return 'MeetingLinkModel(pk: $pk, link: $link, name: $name, hit: $hit, created: $created, creator: $creator)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MeetingLinkModelImpl &&
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

  /// Create a copy of MeetingLinkModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$MeetingLinkModelImplCopyWith<_$MeetingLinkModelImpl> get copyWith =>
      __$$MeetingLinkModelImplCopyWithImpl<_$MeetingLinkModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$MeetingLinkModelImplToJson(this);
  }
}

abstract class _MeetingLinkModel implements MeetingLinkModel {
  const factory _MeetingLinkModel({
    required final int pk,
    required final String link,
    required final String name,
    final int hit,
    required final String created,
    final SimpleUserModel? creator,
  }) = _$MeetingLinkModelImpl;

  factory _MeetingLinkModel.fromJson(Map<String, dynamic> json) =
      _$MeetingLinkModelImpl.fromJson;

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

  /// Create a copy of MeetingLinkModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$MeetingLinkModelImplCopyWith<_$MeetingLinkModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

IssueInMeetingModel _$IssueInMeetingModelFromJson(Map<String, dynamic> json) {
  return _IssueInMeetingModel.fromJson(json);
}

/// @nodoc
mixin _$IssueInMeetingModel {
  int get pk => throw _privateConstructorUsedError;
  String get project => throw _privateConstructorUsedError; // slug
  String get subject => throw _privateConstructorUsedError;
  String get status => throw _privateConstructorUsedError;
  SimpleUserModel? get assignedTo => throw _privateConstructorUsedError;
  String? get closed => throw _privateConstructorUsedError;

  /// Serializes this IssueInMeetingModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of IssueInMeetingModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $IssueInMeetingModelCopyWith<IssueInMeetingModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $IssueInMeetingModelCopyWith<$Res> {
  factory $IssueInMeetingModelCopyWith(
    IssueInMeetingModel value,
    $Res Function(IssueInMeetingModel) then,
  ) = _$IssueInMeetingModelCopyWithImpl<$Res, IssueInMeetingModel>;
  @useResult
  $Res call({
    int pk,
    String project,
    String subject,
    String status,
    SimpleUserModel? assignedTo,
    String? closed,
  });

  $SimpleUserModelCopyWith<$Res>? get assignedTo;
}

/// @nodoc
class _$IssueInMeetingModelCopyWithImpl<$Res, $Val extends IssueInMeetingModel>
    implements $IssueInMeetingModelCopyWith<$Res> {
  _$IssueInMeetingModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of IssueInMeetingModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? project = null,
    Object? subject = null,
    Object? status = null,
    Object? assignedTo = freezed,
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
                      as String,
            subject: null == subject
                ? _value.subject
                : subject // ignore: cast_nullable_to_non_nullable
                      as String,
            status: null == status
                ? _value.status
                : status // ignore: cast_nullable_to_non_nullable
                      as String,
            assignedTo: freezed == assignedTo
                ? _value.assignedTo
                : assignedTo // ignore: cast_nullable_to_non_nullable
                      as SimpleUserModel?,
            closed: freezed == closed
                ? _value.closed
                : closed // ignore: cast_nullable_to_non_nullable
                      as String?,
          )
          as $Val,
    );
  }

  /// Create a copy of IssueInMeetingModel
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
abstract class _$$IssueInMeetingModelImplCopyWith<$Res>
    implements $IssueInMeetingModelCopyWith<$Res> {
  factory _$$IssueInMeetingModelImplCopyWith(
    _$IssueInMeetingModelImpl value,
    $Res Function(_$IssueInMeetingModelImpl) then,
  ) = __$$IssueInMeetingModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int pk,
    String project,
    String subject,
    String status,
    SimpleUserModel? assignedTo,
    String? closed,
  });

  @override
  $SimpleUserModelCopyWith<$Res>? get assignedTo;
}

/// @nodoc
class __$$IssueInMeetingModelImplCopyWithImpl<$Res>
    extends _$IssueInMeetingModelCopyWithImpl<$Res, _$IssueInMeetingModelImpl>
    implements _$$IssueInMeetingModelImplCopyWith<$Res> {
  __$$IssueInMeetingModelImplCopyWithImpl(
    _$IssueInMeetingModelImpl _value,
    $Res Function(_$IssueInMeetingModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of IssueInMeetingModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? project = null,
    Object? subject = null,
    Object? status = null,
    Object? assignedTo = freezed,
    Object? closed = freezed,
  }) {
    return _then(
      _$IssueInMeetingModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        project: null == project
            ? _value.project
            : project // ignore: cast_nullable_to_non_nullable
                  as String,
        subject: null == subject
            ? _value.subject
            : subject // ignore: cast_nullable_to_non_nullable
                  as String,
        status: null == status
            ? _value.status
            : status // ignore: cast_nullable_to_non_nullable
                  as String,
        assignedTo: freezed == assignedTo
            ? _value.assignedTo
            : assignedTo // ignore: cast_nullable_to_non_nullable
                  as SimpleUserModel?,
        closed: freezed == closed
            ? _value.closed
            : closed // ignore: cast_nullable_to_non_nullable
                  as String?,
      ),
    );
  }
}

/// @nodoc
@JsonSerializable()
class _$IssueInMeetingModelImpl implements _IssueInMeetingModel {
  const _$IssueInMeetingModelImpl({
    required this.pk,
    required this.project,
    required this.subject,
    required this.status,
    this.assignedTo,
    this.closed,
  });

  factory _$IssueInMeetingModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$IssueInMeetingModelImplFromJson(json);

  @override
  final int pk;
  @override
  final String project;
  // slug
  @override
  final String subject;
  @override
  final String status;
  @override
  final SimpleUserModel? assignedTo;
  @override
  final String? closed;

  @override
  String toString() {
    return 'IssueInMeetingModel(pk: $pk, project: $project, subject: $subject, status: $status, assignedTo: $assignedTo, closed: $closed)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$IssueInMeetingModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.project, project) || other.project == project) &&
            (identical(other.subject, subject) || other.subject == subject) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.assignedTo, assignedTo) ||
                other.assignedTo == assignedTo) &&
            (identical(other.closed, closed) || other.closed == closed));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
    runtimeType,
    pk,
    project,
    subject,
    status,
    assignedTo,
    closed,
  );

  /// Create a copy of IssueInMeetingModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$IssueInMeetingModelImplCopyWith<_$IssueInMeetingModelImpl> get copyWith =>
      __$$IssueInMeetingModelImplCopyWithImpl<_$IssueInMeetingModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$IssueInMeetingModelImplToJson(this);
  }
}

abstract class _IssueInMeetingModel implements IssueInMeetingModel {
  const factory _IssueInMeetingModel({
    required final int pk,
    required final String project,
    required final String subject,
    required final String status,
    final SimpleUserModel? assignedTo,
    final String? closed,
  }) = _$IssueInMeetingModelImpl;

  factory _IssueInMeetingModel.fromJson(Map<String, dynamic> json) =
      _$IssueInMeetingModelImpl.fromJson;

  @override
  int get pk;
  @override
  String get project; // slug
  @override
  String get subject;
  @override
  String get status;
  @override
  SimpleUserModel? get assignedTo;
  @override
  String? get closed;

  /// Create a copy of IssueInMeetingModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$IssueInMeetingModelImplCopyWith<_$IssueInMeetingModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

MeetingModel _$MeetingModelFromJson(Map<String, dynamic> json) {
  return _MeetingModel.fromJson(json);
}

/// @nodoc
mixin _$MeetingModel {
  int get pk => throw _privateConstructorUsedError;
  int get project => throw _privateConstructorUsedError;
  SimpleProjectModel get projectDesc => throw _privateConstructorUsedError;
  String get title => throw _privateConstructorUsedError;
  int? get category => throw _privateConstructorUsedError;
  MeetingCategoryModel? get categoryDesc => throw _privateConstructorUsedError;
  String get status => throw _privateConstructorUsedError;
  String get statusDisplay => throw _privateConstructorUsedError;
  bool get isConfirmed => throw _privateConstructorUsedError;
  String get agenda => throw _privateConstructorUsedError;
  String get content => throw _privateConstructorUsedError;
  String get decisions => throw _privateConstructorUsedError;
  String get actionItems => throw _privateConstructorUsedError;
  String get meetingDate => throw _privateConstructorUsedError;
  List<int> get attendees => throw _privateConstructorUsedError;
  List<SimpleUserModel> get attendeesDesc => throw _privateConstructorUsedError;
  String get otherAttendees => throw _privateConstructorUsedError;
  List<MeetingFileModel> get files => throw _privateConstructorUsedError;
  List<MeetingLinkModel> get links => throw _privateConstructorUsedError;
  List<IssueInMeetingModel> get issues => throw _privateConstructorUsedError;
  SimpleUserModel? get creator => throw _privateConstructorUsedError;
  SimpleUserModel? get updater => throw _privateConstructorUsedError;
  String get created => throw _privateConstructorUsedError;
  String get updated => throw _privateConstructorUsedError;

  /// Serializes this MeetingModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of MeetingModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $MeetingModelCopyWith<MeetingModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MeetingModelCopyWith<$Res> {
  factory $MeetingModelCopyWith(
    MeetingModel value,
    $Res Function(MeetingModel) then,
  ) = _$MeetingModelCopyWithImpl<$Res, MeetingModel>;
  @useResult
  $Res call({
    int pk,
    int project,
    SimpleProjectModel projectDesc,
    String title,
    int? category,
    MeetingCategoryModel? categoryDesc,
    String status,
    String statusDisplay,
    bool isConfirmed,
    String agenda,
    String content,
    String decisions,
    String actionItems,
    String meetingDate,
    List<int> attendees,
    List<SimpleUserModel> attendeesDesc,
    String otherAttendees,
    List<MeetingFileModel> files,
    List<MeetingLinkModel> links,
    List<IssueInMeetingModel> issues,
    SimpleUserModel? creator,
    SimpleUserModel? updater,
    String created,
    String updated,
  });

  $SimpleProjectModelCopyWith<$Res> get projectDesc;
  $MeetingCategoryModelCopyWith<$Res>? get categoryDesc;
  $SimpleUserModelCopyWith<$Res>? get creator;
  $SimpleUserModelCopyWith<$Res>? get updater;
}

/// @nodoc
class _$MeetingModelCopyWithImpl<$Res, $Val extends MeetingModel>
    implements $MeetingModelCopyWith<$Res> {
  _$MeetingModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of MeetingModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? project = null,
    Object? projectDesc = null,
    Object? title = null,
    Object? category = freezed,
    Object? categoryDesc = freezed,
    Object? status = null,
    Object? statusDisplay = null,
    Object? isConfirmed = null,
    Object? agenda = null,
    Object? content = null,
    Object? decisions = null,
    Object? actionItems = null,
    Object? meetingDate = null,
    Object? attendees = null,
    Object? attendeesDesc = null,
    Object? otherAttendees = null,
    Object? files = null,
    Object? links = null,
    Object? issues = null,
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
                      as int,
            projectDesc: null == projectDesc
                ? _value.projectDesc
                : projectDesc // ignore: cast_nullable_to_non_nullable
                      as SimpleProjectModel,
            title: null == title
                ? _value.title
                : title // ignore: cast_nullable_to_non_nullable
                      as String,
            category: freezed == category
                ? _value.category
                : category // ignore: cast_nullable_to_non_nullable
                      as int?,
            categoryDesc: freezed == categoryDesc
                ? _value.categoryDesc
                : categoryDesc // ignore: cast_nullable_to_non_nullable
                      as MeetingCategoryModel?,
            status: null == status
                ? _value.status
                : status // ignore: cast_nullable_to_non_nullable
                      as String,
            statusDisplay: null == statusDisplay
                ? _value.statusDisplay
                : statusDisplay // ignore: cast_nullable_to_non_nullable
                      as String,
            isConfirmed: null == isConfirmed
                ? _value.isConfirmed
                : isConfirmed // ignore: cast_nullable_to_non_nullable
                      as bool,
            agenda: null == agenda
                ? _value.agenda
                : agenda // ignore: cast_nullable_to_non_nullable
                      as String,
            content: null == content
                ? _value.content
                : content // ignore: cast_nullable_to_non_nullable
                      as String,
            decisions: null == decisions
                ? _value.decisions
                : decisions // ignore: cast_nullable_to_non_nullable
                      as String,
            actionItems: null == actionItems
                ? _value.actionItems
                : actionItems // ignore: cast_nullable_to_non_nullable
                      as String,
            meetingDate: null == meetingDate
                ? _value.meetingDate
                : meetingDate // ignore: cast_nullable_to_non_nullable
                      as String,
            attendees: null == attendees
                ? _value.attendees
                : attendees // ignore: cast_nullable_to_non_nullable
                      as List<int>,
            attendeesDesc: null == attendeesDesc
                ? _value.attendeesDesc
                : attendeesDesc // ignore: cast_nullable_to_non_nullable
                      as List<SimpleUserModel>,
            otherAttendees: null == otherAttendees
                ? _value.otherAttendees
                : otherAttendees // ignore: cast_nullable_to_non_nullable
                      as String,
            files: null == files
                ? _value.files
                : files // ignore: cast_nullable_to_non_nullable
                      as List<MeetingFileModel>,
            links: null == links
                ? _value.links
                : links // ignore: cast_nullable_to_non_nullable
                      as List<MeetingLinkModel>,
            issues: null == issues
                ? _value.issues
                : issues // ignore: cast_nullable_to_non_nullable
                      as List<IssueInMeetingModel>,
            creator: freezed == creator
                ? _value.creator
                : creator // ignore: cast_nullable_to_non_nullable
                      as SimpleUserModel?,
            updater: freezed == updater
                ? _value.updater
                : updater // ignore: cast_nullable_to_non_nullable
                      as SimpleUserModel?,
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

  /// Create a copy of MeetingModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SimpleProjectModelCopyWith<$Res> get projectDesc {
    return $SimpleProjectModelCopyWith<$Res>(_value.projectDesc, (value) {
      return _then(_value.copyWith(projectDesc: value) as $Val);
    });
  }

  /// Create a copy of MeetingModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $MeetingCategoryModelCopyWith<$Res>? get categoryDesc {
    if (_value.categoryDesc == null) {
      return null;
    }

    return $MeetingCategoryModelCopyWith<$Res>(_value.categoryDesc!, (value) {
      return _then(_value.copyWith(categoryDesc: value) as $Val);
    });
  }

  /// Create a copy of MeetingModel
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

  /// Create a copy of MeetingModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SimpleUserModelCopyWith<$Res>? get updater {
    if (_value.updater == null) {
      return null;
    }

    return $SimpleUserModelCopyWith<$Res>(_value.updater!, (value) {
      return _then(_value.copyWith(updater: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$MeetingModelImplCopyWith<$Res>
    implements $MeetingModelCopyWith<$Res> {
  factory _$$MeetingModelImplCopyWith(
    _$MeetingModelImpl value,
    $Res Function(_$MeetingModelImpl) then,
  ) = __$$MeetingModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int pk,
    int project,
    SimpleProjectModel projectDesc,
    String title,
    int? category,
    MeetingCategoryModel? categoryDesc,
    String status,
    String statusDisplay,
    bool isConfirmed,
    String agenda,
    String content,
    String decisions,
    String actionItems,
    String meetingDate,
    List<int> attendees,
    List<SimpleUserModel> attendeesDesc,
    String otherAttendees,
    List<MeetingFileModel> files,
    List<MeetingLinkModel> links,
    List<IssueInMeetingModel> issues,
    SimpleUserModel? creator,
    SimpleUserModel? updater,
    String created,
    String updated,
  });

  @override
  $SimpleProjectModelCopyWith<$Res> get projectDesc;
  @override
  $MeetingCategoryModelCopyWith<$Res>? get categoryDesc;
  @override
  $SimpleUserModelCopyWith<$Res>? get creator;
  @override
  $SimpleUserModelCopyWith<$Res>? get updater;
}

/// @nodoc
class __$$MeetingModelImplCopyWithImpl<$Res>
    extends _$MeetingModelCopyWithImpl<$Res, _$MeetingModelImpl>
    implements _$$MeetingModelImplCopyWith<$Res> {
  __$$MeetingModelImplCopyWithImpl(
    _$MeetingModelImpl _value,
    $Res Function(_$MeetingModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of MeetingModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? project = null,
    Object? projectDesc = null,
    Object? title = null,
    Object? category = freezed,
    Object? categoryDesc = freezed,
    Object? status = null,
    Object? statusDisplay = null,
    Object? isConfirmed = null,
    Object? agenda = null,
    Object? content = null,
    Object? decisions = null,
    Object? actionItems = null,
    Object? meetingDate = null,
    Object? attendees = null,
    Object? attendeesDesc = null,
    Object? otherAttendees = null,
    Object? files = null,
    Object? links = null,
    Object? issues = null,
    Object? creator = freezed,
    Object? updater = freezed,
    Object? created = null,
    Object? updated = null,
  }) {
    return _then(
      _$MeetingModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        project: null == project
            ? _value.project
            : project // ignore: cast_nullable_to_non_nullable
                  as int,
        projectDesc: null == projectDesc
            ? _value.projectDesc
            : projectDesc // ignore: cast_nullable_to_non_nullable
                  as SimpleProjectModel,
        title: null == title
            ? _value.title
            : title // ignore: cast_nullable_to_non_nullable
                  as String,
        category: freezed == category
            ? _value.category
            : category // ignore: cast_nullable_to_non_nullable
                  as int?,
        categoryDesc: freezed == categoryDesc
            ? _value.categoryDesc
            : categoryDesc // ignore: cast_nullable_to_non_nullable
                  as MeetingCategoryModel?,
        status: null == status
            ? _value.status
            : status // ignore: cast_nullable_to_non_nullable
                  as String,
        statusDisplay: null == statusDisplay
            ? _value.statusDisplay
            : statusDisplay // ignore: cast_nullable_to_non_nullable
                  as String,
        isConfirmed: null == isConfirmed
            ? _value.isConfirmed
            : isConfirmed // ignore: cast_nullable_to_non_nullable
                  as bool,
        agenda: null == agenda
            ? _value.agenda
            : agenda // ignore: cast_nullable_to_non_nullable
                  as String,
        content: null == content
            ? _value.content
            : content // ignore: cast_nullable_to_non_nullable
                  as String,
        decisions: null == decisions
            ? _value.decisions
            : decisions // ignore: cast_nullable_to_non_nullable
                  as String,
        actionItems: null == actionItems
            ? _value.actionItems
            : actionItems // ignore: cast_nullable_to_non_nullable
                  as String,
        meetingDate: null == meetingDate
            ? _value.meetingDate
            : meetingDate // ignore: cast_nullable_to_non_nullable
                  as String,
        attendees: null == attendees
            ? _value._attendees
            : attendees // ignore: cast_nullable_to_non_nullable
                  as List<int>,
        attendeesDesc: null == attendeesDesc
            ? _value._attendeesDesc
            : attendeesDesc // ignore: cast_nullable_to_non_nullable
                  as List<SimpleUserModel>,
        otherAttendees: null == otherAttendees
            ? _value.otherAttendees
            : otherAttendees // ignore: cast_nullable_to_non_nullable
                  as String,
        files: null == files
            ? _value._files
            : files // ignore: cast_nullable_to_non_nullable
                  as List<MeetingFileModel>,
        links: null == links
            ? _value._links
            : links // ignore: cast_nullable_to_non_nullable
                  as List<MeetingLinkModel>,
        issues: null == issues
            ? _value._issues
            : issues // ignore: cast_nullable_to_non_nullable
                  as List<IssueInMeetingModel>,
        creator: freezed == creator
            ? _value.creator
            : creator // ignore: cast_nullable_to_non_nullable
                  as SimpleUserModel?,
        updater: freezed == updater
            ? _value.updater
            : updater // ignore: cast_nullable_to_non_nullable
                  as SimpleUserModel?,
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
@JsonSerializable()
class _$MeetingModelImpl implements _MeetingModel {
  const _$MeetingModelImpl({
    required this.pk,
    required this.project,
    required this.projectDesc,
    required this.title,
    this.category,
    this.categoryDesc,
    this.status = '1',
    this.statusDisplay = '예정',
    this.isConfirmed = false,
    this.agenda = '',
    this.content = '',
    this.decisions = '',
    this.actionItems = '',
    required this.meetingDate,
    final List<int> attendees = const [],
    final List<SimpleUserModel> attendeesDesc = const [],
    this.otherAttendees = '',
    final List<MeetingFileModel> files = const [],
    final List<MeetingLinkModel> links = const [],
    final List<IssueInMeetingModel> issues = const [],
    this.creator,
    this.updater,
    required this.created,
    required this.updated,
  }) : _attendees = attendees,
       _attendeesDesc = attendeesDesc,
       _files = files,
       _links = links,
       _issues = issues;

  factory _$MeetingModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$MeetingModelImplFromJson(json);

  @override
  final int pk;
  @override
  final int project;
  @override
  final SimpleProjectModel projectDesc;
  @override
  final String title;
  @override
  final int? category;
  @override
  final MeetingCategoryModel? categoryDesc;
  @override
  @JsonKey()
  final String status;
  @override
  @JsonKey()
  final String statusDisplay;
  @override
  @JsonKey()
  final bool isConfirmed;
  @override
  @JsonKey()
  final String agenda;
  @override
  @JsonKey()
  final String content;
  @override
  @JsonKey()
  final String decisions;
  @override
  @JsonKey()
  final String actionItems;
  @override
  final String meetingDate;
  final List<int> _attendees;
  @override
  @JsonKey()
  List<int> get attendees {
    if (_attendees is EqualUnmodifiableListView) return _attendees;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_attendees);
  }

  final List<SimpleUserModel> _attendeesDesc;
  @override
  @JsonKey()
  List<SimpleUserModel> get attendeesDesc {
    if (_attendeesDesc is EqualUnmodifiableListView) return _attendeesDesc;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_attendeesDesc);
  }

  @override
  @JsonKey()
  final String otherAttendees;
  final List<MeetingFileModel> _files;
  @override
  @JsonKey()
  List<MeetingFileModel> get files {
    if (_files is EqualUnmodifiableListView) return _files;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_files);
  }

  final List<MeetingLinkModel> _links;
  @override
  @JsonKey()
  List<MeetingLinkModel> get links {
    if (_links is EqualUnmodifiableListView) return _links;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_links);
  }

  final List<IssueInMeetingModel> _issues;
  @override
  @JsonKey()
  List<IssueInMeetingModel> get issues {
    if (_issues is EqualUnmodifiableListView) return _issues;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_issues);
  }

  @override
  final SimpleUserModel? creator;
  @override
  final SimpleUserModel? updater;
  @override
  final String created;
  @override
  final String updated;

  @override
  String toString() {
    return 'MeetingModel(pk: $pk, project: $project, projectDesc: $projectDesc, title: $title, category: $category, categoryDesc: $categoryDesc, status: $status, statusDisplay: $statusDisplay, isConfirmed: $isConfirmed, agenda: $agenda, content: $content, decisions: $decisions, actionItems: $actionItems, meetingDate: $meetingDate, attendees: $attendees, attendeesDesc: $attendeesDesc, otherAttendees: $otherAttendees, files: $files, links: $links, issues: $issues, creator: $creator, updater: $updater, created: $created, updated: $updated)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MeetingModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.project, project) || other.project == project) &&
            (identical(other.projectDesc, projectDesc) ||
                other.projectDesc == projectDesc) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.category, category) ||
                other.category == category) &&
            (identical(other.categoryDesc, categoryDesc) ||
                other.categoryDesc == categoryDesc) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.statusDisplay, statusDisplay) ||
                other.statusDisplay == statusDisplay) &&
            (identical(other.isConfirmed, isConfirmed) ||
                other.isConfirmed == isConfirmed) &&
            (identical(other.agenda, agenda) || other.agenda == agenda) &&
            (identical(other.content, content) || other.content == content) &&
            (identical(other.decisions, decisions) ||
                other.decisions == decisions) &&
            (identical(other.actionItems, actionItems) ||
                other.actionItems == actionItems) &&
            (identical(other.meetingDate, meetingDate) ||
                other.meetingDate == meetingDate) &&
            const DeepCollectionEquality().equals(
              other._attendees,
              _attendees,
            ) &&
            const DeepCollectionEquality().equals(
              other._attendeesDesc,
              _attendeesDesc,
            ) &&
            (identical(other.otherAttendees, otherAttendees) ||
                other.otherAttendees == otherAttendees) &&
            const DeepCollectionEquality().equals(other._files, _files) &&
            const DeepCollectionEquality().equals(other._links, _links) &&
            const DeepCollectionEquality().equals(other._issues, _issues) &&
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
    projectDesc,
    title,
    category,
    categoryDesc,
    status,
    statusDisplay,
    isConfirmed,
    agenda,
    content,
    decisions,
    actionItems,
    meetingDate,
    const DeepCollectionEquality().hash(_attendees),
    const DeepCollectionEquality().hash(_attendeesDesc),
    otherAttendees,
    const DeepCollectionEquality().hash(_files),
    const DeepCollectionEquality().hash(_links),
    const DeepCollectionEquality().hash(_issues),
    creator,
    updater,
    created,
    updated,
  ]);

  /// Create a copy of MeetingModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$MeetingModelImplCopyWith<_$MeetingModelImpl> get copyWith =>
      __$$MeetingModelImplCopyWithImpl<_$MeetingModelImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$MeetingModelImplToJson(this);
  }
}

abstract class _MeetingModel implements MeetingModel {
  const factory _MeetingModel({
    required final int pk,
    required final int project,
    required final SimpleProjectModel projectDesc,
    required final String title,
    final int? category,
    final MeetingCategoryModel? categoryDesc,
    final String status,
    final String statusDisplay,
    final bool isConfirmed,
    final String agenda,
    final String content,
    final String decisions,
    final String actionItems,
    required final String meetingDate,
    final List<int> attendees,
    final List<SimpleUserModel> attendeesDesc,
    final String otherAttendees,
    final List<MeetingFileModel> files,
    final List<MeetingLinkModel> links,
    final List<IssueInMeetingModel> issues,
    final SimpleUserModel? creator,
    final SimpleUserModel? updater,
    required final String created,
    required final String updated,
  }) = _$MeetingModelImpl;

  factory _MeetingModel.fromJson(Map<String, dynamic> json) =
      _$MeetingModelImpl.fromJson;

  @override
  int get pk;
  @override
  int get project;
  @override
  SimpleProjectModel get projectDesc;
  @override
  String get title;
  @override
  int? get category;
  @override
  MeetingCategoryModel? get categoryDesc;
  @override
  String get status;
  @override
  String get statusDisplay;
  @override
  bool get isConfirmed;
  @override
  String get agenda;
  @override
  String get content;
  @override
  String get decisions;
  @override
  String get actionItems;
  @override
  String get meetingDate;
  @override
  List<int> get attendees;
  @override
  List<SimpleUserModel> get attendeesDesc;
  @override
  String get otherAttendees;
  @override
  List<MeetingFileModel> get files;
  @override
  List<MeetingLinkModel> get links;
  @override
  List<IssueInMeetingModel> get issues;
  @override
  SimpleUserModel? get creator;
  @override
  SimpleUserModel? get updater;
  @override
  String get created;
  @override
  String get updated;

  /// Create a copy of MeetingModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$MeetingModelImplCopyWith<_$MeetingModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

MeetingListResponse _$MeetingListResponseFromJson(Map<String, dynamic> json) {
  return _MeetingListResponse.fromJson(json);
}

/// @nodoc
mixin _$MeetingListResponse {
  int get count => throw _privateConstructorUsedError;
  String? get next => throw _privateConstructorUsedError;
  String? get previous => throw _privateConstructorUsedError;
  List<MeetingModel> get results => throw _privateConstructorUsedError;

  /// Serializes this MeetingListResponse to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of MeetingListResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $MeetingListResponseCopyWith<MeetingListResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MeetingListResponseCopyWith<$Res> {
  factory $MeetingListResponseCopyWith(
    MeetingListResponse value,
    $Res Function(MeetingListResponse) then,
  ) = _$MeetingListResponseCopyWithImpl<$Res, MeetingListResponse>;
  @useResult
  $Res call({
    int count,
    String? next,
    String? previous,
    List<MeetingModel> results,
  });
}

/// @nodoc
class _$MeetingListResponseCopyWithImpl<$Res, $Val extends MeetingListResponse>
    implements $MeetingListResponseCopyWith<$Res> {
  _$MeetingListResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of MeetingListResponse
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
                      as List<MeetingModel>,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$MeetingListResponseImplCopyWith<$Res>
    implements $MeetingListResponseCopyWith<$Res> {
  factory _$$MeetingListResponseImplCopyWith(
    _$MeetingListResponseImpl value,
    $Res Function(_$MeetingListResponseImpl) then,
  ) = __$$MeetingListResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int count,
    String? next,
    String? previous,
    List<MeetingModel> results,
  });
}

/// @nodoc
class __$$MeetingListResponseImplCopyWithImpl<$Res>
    extends _$MeetingListResponseCopyWithImpl<$Res, _$MeetingListResponseImpl>
    implements _$$MeetingListResponseImplCopyWith<$Res> {
  __$$MeetingListResponseImplCopyWithImpl(
    _$MeetingListResponseImpl _value,
    $Res Function(_$MeetingListResponseImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of MeetingListResponse
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
      _$MeetingListResponseImpl(
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
                  as List<MeetingModel>,
      ),
    );
  }
}

/// @nodoc
@JsonSerializable()
class _$MeetingListResponseImpl implements _MeetingListResponse {
  const _$MeetingListResponseImpl({
    required this.count,
    this.next,
    this.previous,
    required final List<MeetingModel> results,
  }) : _results = results;

  factory _$MeetingListResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$MeetingListResponseImplFromJson(json);

  @override
  final int count;
  @override
  final String? next;
  @override
  final String? previous;
  final List<MeetingModel> _results;
  @override
  List<MeetingModel> get results {
    if (_results is EqualUnmodifiableListView) return _results;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_results);
  }

  @override
  String toString() {
    return 'MeetingListResponse(count: $count, next: $next, previous: $previous, results: $results)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MeetingListResponseImpl &&
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

  /// Create a copy of MeetingListResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$MeetingListResponseImplCopyWith<_$MeetingListResponseImpl> get copyWith =>
      __$$MeetingListResponseImplCopyWithImpl<_$MeetingListResponseImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$MeetingListResponseImplToJson(this);
  }
}

abstract class _MeetingListResponse implements MeetingListResponse {
  const factory _MeetingListResponse({
    required final int count,
    final String? next,
    final String? previous,
    required final List<MeetingModel> results,
  }) = _$MeetingListResponseImpl;

  factory _MeetingListResponse.fromJson(Map<String, dynamic> json) =
      _$MeetingListResponseImpl.fromJson;

  @override
  int get count;
  @override
  String? get next;
  @override
  String? get previous;
  @override
  List<MeetingModel> get results;

  /// Create a copy of MeetingListResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$MeetingListResponseImplCopyWith<_$MeetingListResponseImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
