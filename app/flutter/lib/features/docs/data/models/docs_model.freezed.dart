// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'docs_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
  'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models',
);

DocCategoryModel _$DocCategoryModelFromJson(Map<String, dynamic> json) {
  return _DocCategoryModel.fromJson(json);
}

/// @nodoc
mixin _$DocCategoryModel {
  int get pk => throw _privateConstructorUsedError;
  String? get docType => throw _privateConstructorUsedError;
  String? get color => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  int? get parent => throw _privateConstructorUsedError;
  int get order => throw _privateConstructorUsedError;
  bool get active => throw _privateConstructorUsedError;
  bool get defaultVal => throw _privateConstructorUsedError;

  /// Serializes this DocCategoryModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of DocCategoryModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $DocCategoryModelCopyWith<DocCategoryModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $DocCategoryModelCopyWith<$Res> {
  factory $DocCategoryModelCopyWith(
    DocCategoryModel value,
    $Res Function(DocCategoryModel) then,
  ) = _$DocCategoryModelCopyWithImpl<$Res, DocCategoryModel>;
  @useResult
  $Res call({
    int pk,
    String? docType,
    String? color,
    String name,
    int? parent,
    int order,
    bool active,
    bool defaultVal,
  });
}

/// @nodoc
class _$DocCategoryModelCopyWithImpl<$Res, $Val extends DocCategoryModel>
    implements $DocCategoryModelCopyWith<$Res> {
  _$DocCategoryModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of DocCategoryModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? docType = freezed,
    Object? color = freezed,
    Object? name = null,
    Object? parent = freezed,
    Object? order = null,
    Object? active = null,
    Object? defaultVal = null,
  }) {
    return _then(
      _value.copyWith(
            pk: null == pk
                ? _value.pk
                : pk // ignore: cast_nullable_to_non_nullable
                      as int,
            docType: freezed == docType
                ? _value.docType
                : docType // ignore: cast_nullable_to_non_nullable
                      as String?,
            color: freezed == color
                ? _value.color
                : color // ignore: cast_nullable_to_non_nullable
                      as String?,
            name: null == name
                ? _value.name
                : name // ignore: cast_nullable_to_non_nullable
                      as String,
            parent: freezed == parent
                ? _value.parent
                : parent // ignore: cast_nullable_to_non_nullable
                      as int?,
            order: null == order
                ? _value.order
                : order // ignore: cast_nullable_to_non_nullable
                      as int,
            active: null == active
                ? _value.active
                : active // ignore: cast_nullable_to_non_nullable
                      as bool,
            defaultVal: null == defaultVal
                ? _value.defaultVal
                : defaultVal // ignore: cast_nullable_to_non_nullable
                      as bool,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$DocCategoryModelImplCopyWith<$Res>
    implements $DocCategoryModelCopyWith<$Res> {
  factory _$$DocCategoryModelImplCopyWith(
    _$DocCategoryModelImpl value,
    $Res Function(_$DocCategoryModelImpl) then,
  ) = __$$DocCategoryModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int pk,
    String? docType,
    String? color,
    String name,
    int? parent,
    int order,
    bool active,
    bool defaultVal,
  });
}

/// @nodoc
class __$$DocCategoryModelImplCopyWithImpl<$Res>
    extends _$DocCategoryModelCopyWithImpl<$Res, _$DocCategoryModelImpl>
    implements _$$DocCategoryModelImplCopyWith<$Res> {
  __$$DocCategoryModelImplCopyWithImpl(
    _$DocCategoryModelImpl _value,
    $Res Function(_$DocCategoryModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of DocCategoryModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? docType = freezed,
    Object? color = freezed,
    Object? name = null,
    Object? parent = freezed,
    Object? order = null,
    Object? active = null,
    Object? defaultVal = null,
  }) {
    return _then(
      _$DocCategoryModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        docType: freezed == docType
            ? _value.docType
            : docType // ignore: cast_nullable_to_non_nullable
                  as String?,
        color: freezed == color
            ? _value.color
            : color // ignore: cast_nullable_to_non_nullable
                  as String?,
        name: null == name
            ? _value.name
            : name // ignore: cast_nullable_to_non_nullable
                  as String,
        parent: freezed == parent
            ? _value.parent
            : parent // ignore: cast_nullable_to_non_nullable
                  as int?,
        order: null == order
            ? _value.order
            : order // ignore: cast_nullable_to_non_nullable
                  as int,
        active: null == active
            ? _value.active
            : active // ignore: cast_nullable_to_non_nullable
                  as bool,
        defaultVal: null == defaultVal
            ? _value.defaultVal
            : defaultVal // ignore: cast_nullable_to_non_nullable
                  as bool,
      ),
    );
  }
}

/// @nodoc
@JsonSerializable()
class _$DocCategoryModelImpl implements _DocCategoryModel {
  const _$DocCategoryModelImpl({
    required this.pk,
    this.docType,
    this.color,
    required this.name,
    this.parent,
    this.order = 0,
    this.active = true,
    this.defaultVal = false,
  });

  factory _$DocCategoryModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$DocCategoryModelImplFromJson(json);

  @override
  final int pk;
  @override
  final String? docType;
  @override
  final String? color;
  @override
  final String name;
  @override
  final int? parent;
  @override
  @JsonKey()
  final int order;
  @override
  @JsonKey()
  final bool active;
  @override
  @JsonKey()
  final bool defaultVal;

  @override
  String toString() {
    return 'DocCategoryModel(pk: $pk, docType: $docType, color: $color, name: $name, parent: $parent, order: $order, active: $active, defaultVal: $defaultVal)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$DocCategoryModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.docType, docType) || other.docType == docType) &&
            (identical(other.color, color) || other.color == color) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.parent, parent) || other.parent == parent) &&
            (identical(other.order, order) || other.order == order) &&
            (identical(other.active, active) || other.active == active) &&
            (identical(other.defaultVal, defaultVal) ||
                other.defaultVal == defaultVal));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
    runtimeType,
    pk,
    docType,
    color,
    name,
    parent,
    order,
    active,
    defaultVal,
  );

  /// Create a copy of DocCategoryModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$DocCategoryModelImplCopyWith<_$DocCategoryModelImpl> get copyWith =>
      __$$DocCategoryModelImplCopyWithImpl<_$DocCategoryModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$DocCategoryModelImplToJson(this);
  }
}

abstract class _DocCategoryModel implements DocCategoryModel {
  const factory _DocCategoryModel({
    required final int pk,
    final String? docType,
    final String? color,
    required final String name,
    final int? parent,
    final int order,
    final bool active,
    final bool defaultVal,
  }) = _$DocCategoryModelImpl;

  factory _DocCategoryModel.fromJson(Map<String, dynamic> json) =
      _$DocCategoryModelImpl.fromJson;

  @override
  int get pk;
  @override
  String? get docType;
  @override
  String? get color;
  @override
  String get name;
  @override
  int? get parent;
  @override
  int get order;
  @override
  bool get active;
  @override
  bool get defaultVal;

  /// Create a copy of DocCategoryModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$DocCategoryModelImplCopyWith<_$DocCategoryModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

DocFileModel _$DocFileModelFromJson(Map<String, dynamic> json) {
  return _DocFileModel.fromJson(json);
}

/// @nodoc
mixin _$DocFileModel {
  int get pk => throw _privateConstructorUsedError;
  int? get docs => throw _privateConstructorUsedError;
  String? get fileName => throw _privateConstructorUsedError;
  String? get file => throw _privateConstructorUsedError;
  String? get fileType => throw _privateConstructorUsedError;
  int? get fileSize => throw _privateConstructorUsedError;
  String? get description => throw _privateConstructorUsedError;
  String? get creator => throw _privateConstructorUsedError;
  int get hit => throw _privateConstructorUsedError;
  String? get created => throw _privateConstructorUsedError;

  /// Serializes this DocFileModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of DocFileModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $DocFileModelCopyWith<DocFileModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $DocFileModelCopyWith<$Res> {
  factory $DocFileModelCopyWith(
    DocFileModel value,
    $Res Function(DocFileModel) then,
  ) = _$DocFileModelCopyWithImpl<$Res, DocFileModel>;
  @useResult
  $Res call({
    int pk,
    int? docs,
    String? fileName,
    String? file,
    String? fileType,
    int? fileSize,
    String? description,
    String? creator,
    int hit,
    String? created,
  });
}

/// @nodoc
class _$DocFileModelCopyWithImpl<$Res, $Val extends DocFileModel>
    implements $DocFileModelCopyWith<$Res> {
  _$DocFileModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of DocFileModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? docs = freezed,
    Object? fileName = freezed,
    Object? file = freezed,
    Object? fileType = freezed,
    Object? fileSize = freezed,
    Object? description = freezed,
    Object? creator = freezed,
    Object? hit = null,
    Object? created = freezed,
  }) {
    return _then(
      _value.copyWith(
            pk: null == pk
                ? _value.pk
                : pk // ignore: cast_nullable_to_non_nullable
                      as int,
            docs: freezed == docs
                ? _value.docs
                : docs // ignore: cast_nullable_to_non_nullable
                      as int?,
            fileName: freezed == fileName
                ? _value.fileName
                : fileName // ignore: cast_nullable_to_non_nullable
                      as String?,
            file: freezed == file
                ? _value.file
                : file // ignore: cast_nullable_to_non_nullable
                      as String?,
            fileType: freezed == fileType
                ? _value.fileType
                : fileType // ignore: cast_nullable_to_non_nullable
                      as String?,
            fileSize: freezed == fileSize
                ? _value.fileSize
                : fileSize // ignore: cast_nullable_to_non_nullable
                      as int?,
            description: freezed == description
                ? _value.description
                : description // ignore: cast_nullable_to_non_nullable
                      as String?,
            creator: freezed == creator
                ? _value.creator
                : creator // ignore: cast_nullable_to_non_nullable
                      as String?,
            hit: null == hit
                ? _value.hit
                : hit // ignore: cast_nullable_to_non_nullable
                      as int,
            created: freezed == created
                ? _value.created
                : created // ignore: cast_nullable_to_non_nullable
                      as String?,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$DocFileModelImplCopyWith<$Res>
    implements $DocFileModelCopyWith<$Res> {
  factory _$$DocFileModelImplCopyWith(
    _$DocFileModelImpl value,
    $Res Function(_$DocFileModelImpl) then,
  ) = __$$DocFileModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int pk,
    int? docs,
    String? fileName,
    String? file,
    String? fileType,
    int? fileSize,
    String? description,
    String? creator,
    int hit,
    String? created,
  });
}

/// @nodoc
class __$$DocFileModelImplCopyWithImpl<$Res>
    extends _$DocFileModelCopyWithImpl<$Res, _$DocFileModelImpl>
    implements _$$DocFileModelImplCopyWith<$Res> {
  __$$DocFileModelImplCopyWithImpl(
    _$DocFileModelImpl _value,
    $Res Function(_$DocFileModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of DocFileModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? docs = freezed,
    Object? fileName = freezed,
    Object? file = freezed,
    Object? fileType = freezed,
    Object? fileSize = freezed,
    Object? description = freezed,
    Object? creator = freezed,
    Object? hit = null,
    Object? created = freezed,
  }) {
    return _then(
      _$DocFileModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        docs: freezed == docs
            ? _value.docs
            : docs // ignore: cast_nullable_to_non_nullable
                  as int?,
        fileName: freezed == fileName
            ? _value.fileName
            : fileName // ignore: cast_nullable_to_non_nullable
                  as String?,
        file: freezed == file
            ? _value.file
            : file // ignore: cast_nullable_to_non_nullable
                  as String?,
        fileType: freezed == fileType
            ? _value.fileType
            : fileType // ignore: cast_nullable_to_non_nullable
                  as String?,
        fileSize: freezed == fileSize
            ? _value.fileSize
            : fileSize // ignore: cast_nullable_to_non_nullable
                  as int?,
        description: freezed == description
            ? _value.description
            : description // ignore: cast_nullable_to_non_nullable
                  as String?,
        creator: freezed == creator
            ? _value.creator
            : creator // ignore: cast_nullable_to_non_nullable
                  as String?,
        hit: null == hit
            ? _value.hit
            : hit // ignore: cast_nullable_to_non_nullable
                  as int,
        created: freezed == created
            ? _value.created
            : created // ignore: cast_nullable_to_non_nullable
                  as String?,
      ),
    );
  }
}

/// @nodoc
@JsonSerializable()
class _$DocFileModelImpl implements _DocFileModel {
  const _$DocFileModelImpl({
    required this.pk,
    this.docs,
    this.fileName,
    this.file,
    this.fileType,
    this.fileSize,
    this.description,
    this.creator,
    this.hit = 0,
    this.created,
  });

  factory _$DocFileModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$DocFileModelImplFromJson(json);

  @override
  final int pk;
  @override
  final int? docs;
  @override
  final String? fileName;
  @override
  final String? file;
  @override
  final String? fileType;
  @override
  final int? fileSize;
  @override
  final String? description;
  @override
  final String? creator;
  @override
  @JsonKey()
  final int hit;
  @override
  final String? created;

  @override
  String toString() {
    return 'DocFileModel(pk: $pk, docs: $docs, fileName: $fileName, file: $file, fileType: $fileType, fileSize: $fileSize, description: $description, creator: $creator, hit: $hit, created: $created)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$DocFileModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.docs, docs) || other.docs == docs) &&
            (identical(other.fileName, fileName) ||
                other.fileName == fileName) &&
            (identical(other.file, file) || other.file == file) &&
            (identical(other.fileType, fileType) ||
                other.fileType == fileType) &&
            (identical(other.fileSize, fileSize) ||
                other.fileSize == fileSize) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.creator, creator) || other.creator == creator) &&
            (identical(other.hit, hit) || other.hit == hit) &&
            (identical(other.created, created) || other.created == created));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
    runtimeType,
    pk,
    docs,
    fileName,
    file,
    fileType,
    fileSize,
    description,
    creator,
    hit,
    created,
  );

  /// Create a copy of DocFileModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$DocFileModelImplCopyWith<_$DocFileModelImpl> get copyWith =>
      __$$DocFileModelImplCopyWithImpl<_$DocFileModelImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$DocFileModelImplToJson(this);
  }
}

abstract class _DocFileModel implements DocFileModel {
  const factory _DocFileModel({
    required final int pk,
    final int? docs,
    final String? fileName,
    final String? file,
    final String? fileType,
    final int? fileSize,
    final String? description,
    final String? creator,
    final int hit,
    final String? created,
  }) = _$DocFileModelImpl;

  factory _DocFileModel.fromJson(Map<String, dynamic> json) =
      _$DocFileModelImpl.fromJson;

  @override
  int get pk;
  @override
  int? get docs;
  @override
  String? get fileName;
  @override
  String? get file;
  @override
  String? get fileType;
  @override
  int? get fileSize;
  @override
  String? get description;
  @override
  String? get creator;
  @override
  int get hit;
  @override
  String? get created;

  /// Create a copy of DocFileModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$DocFileModelImplCopyWith<_$DocFileModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

DocLinkModel _$DocLinkModelFromJson(Map<String, dynamic> json) {
  return _DocLinkModel.fromJson(json);
}

/// @nodoc
mixin _$DocLinkModel {
  int get pk => throw _privateConstructorUsedError;
  int? get docs => throw _privateConstructorUsedError;
  String get link => throw _privateConstructorUsedError;
  String? get description => throw _privateConstructorUsedError;
  String? get creator => throw _privateConstructorUsedError;
  int get hit => throw _privateConstructorUsedError;
  String? get created => throw _privateConstructorUsedError;

  /// Serializes this DocLinkModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of DocLinkModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $DocLinkModelCopyWith<DocLinkModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $DocLinkModelCopyWith<$Res> {
  factory $DocLinkModelCopyWith(
    DocLinkModel value,
    $Res Function(DocLinkModel) then,
  ) = _$DocLinkModelCopyWithImpl<$Res, DocLinkModel>;
  @useResult
  $Res call({
    int pk,
    int? docs,
    String link,
    String? description,
    String? creator,
    int hit,
    String? created,
  });
}

/// @nodoc
class _$DocLinkModelCopyWithImpl<$Res, $Val extends DocLinkModel>
    implements $DocLinkModelCopyWith<$Res> {
  _$DocLinkModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of DocLinkModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? docs = freezed,
    Object? link = null,
    Object? description = freezed,
    Object? creator = freezed,
    Object? hit = null,
    Object? created = freezed,
  }) {
    return _then(
      _value.copyWith(
            pk: null == pk
                ? _value.pk
                : pk // ignore: cast_nullable_to_non_nullable
                      as int,
            docs: freezed == docs
                ? _value.docs
                : docs // ignore: cast_nullable_to_non_nullable
                      as int?,
            link: null == link
                ? _value.link
                : link // ignore: cast_nullable_to_non_nullable
                      as String,
            description: freezed == description
                ? _value.description
                : description // ignore: cast_nullable_to_non_nullable
                      as String?,
            creator: freezed == creator
                ? _value.creator
                : creator // ignore: cast_nullable_to_non_nullable
                      as String?,
            hit: null == hit
                ? _value.hit
                : hit // ignore: cast_nullable_to_non_nullable
                      as int,
            created: freezed == created
                ? _value.created
                : created // ignore: cast_nullable_to_non_nullable
                      as String?,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$DocLinkModelImplCopyWith<$Res>
    implements $DocLinkModelCopyWith<$Res> {
  factory _$$DocLinkModelImplCopyWith(
    _$DocLinkModelImpl value,
    $Res Function(_$DocLinkModelImpl) then,
  ) = __$$DocLinkModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int pk,
    int? docs,
    String link,
    String? description,
    String? creator,
    int hit,
    String? created,
  });
}

/// @nodoc
class __$$DocLinkModelImplCopyWithImpl<$Res>
    extends _$DocLinkModelCopyWithImpl<$Res, _$DocLinkModelImpl>
    implements _$$DocLinkModelImplCopyWith<$Res> {
  __$$DocLinkModelImplCopyWithImpl(
    _$DocLinkModelImpl _value,
    $Res Function(_$DocLinkModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of DocLinkModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? docs = freezed,
    Object? link = null,
    Object? description = freezed,
    Object? creator = freezed,
    Object? hit = null,
    Object? created = freezed,
  }) {
    return _then(
      _$DocLinkModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        docs: freezed == docs
            ? _value.docs
            : docs // ignore: cast_nullable_to_non_nullable
                  as int?,
        link: null == link
            ? _value.link
            : link // ignore: cast_nullable_to_non_nullable
                  as String,
        description: freezed == description
            ? _value.description
            : description // ignore: cast_nullable_to_non_nullable
                  as String?,
        creator: freezed == creator
            ? _value.creator
            : creator // ignore: cast_nullable_to_non_nullable
                  as String?,
        hit: null == hit
            ? _value.hit
            : hit // ignore: cast_nullable_to_non_nullable
                  as int,
        created: freezed == created
            ? _value.created
            : created // ignore: cast_nullable_to_non_nullable
                  as String?,
      ),
    );
  }
}

/// @nodoc
@JsonSerializable()
class _$DocLinkModelImpl implements _DocLinkModel {
  const _$DocLinkModelImpl({
    required this.pk,
    this.docs,
    required this.link,
    this.description,
    this.creator,
    this.hit = 0,
    this.created,
  });

  factory _$DocLinkModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$DocLinkModelImplFromJson(json);

  @override
  final int pk;
  @override
  final int? docs;
  @override
  final String link;
  @override
  final String? description;
  @override
  final String? creator;
  @override
  @JsonKey()
  final int hit;
  @override
  final String? created;

  @override
  String toString() {
    return 'DocLinkModel(pk: $pk, docs: $docs, link: $link, description: $description, creator: $creator, hit: $hit, created: $created)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$DocLinkModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.docs, docs) || other.docs == docs) &&
            (identical(other.link, link) || other.link == link) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.creator, creator) || other.creator == creator) &&
            (identical(other.hit, hit) || other.hit == hit) &&
            (identical(other.created, created) || other.created == created));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
    runtimeType,
    pk,
    docs,
    link,
    description,
    creator,
    hit,
    created,
  );

  /// Create a copy of DocLinkModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$DocLinkModelImplCopyWith<_$DocLinkModelImpl> get copyWith =>
      __$$DocLinkModelImplCopyWithImpl<_$DocLinkModelImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$DocLinkModelImplToJson(this);
  }
}

abstract class _DocLinkModel implements DocLinkModel {
  const factory _DocLinkModel({
    required final int pk,
    final int? docs,
    required final String link,
    final String? description,
    final String? creator,
    final int hit,
    final String? created,
  }) = _$DocLinkModelImpl;

  factory _DocLinkModel.fromJson(Map<String, dynamic> json) =
      _$DocLinkModelImpl.fromJson;

  @override
  int get pk;
  @override
  int? get docs;
  @override
  String get link;
  @override
  String? get description;
  @override
  String? get creator;
  @override
  int get hit;
  @override
  String? get created;

  /// Create a copy of DocLinkModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$DocLinkModelImplCopyWith<_$DocLinkModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

DocumentModel _$DocumentModelFromJson(Map<String, dynamic> json) {
  return _DocumentModel.fromJson(json);
}

/// @nodoc
mixin _$DocumentModel {
  int get pk => throw _privateConstructorUsedError;
  SimpleProjectModel? get project => throw _privateConstructorUsedError;
  String? get projType => throw _privateConstructorUsedError;
  String? get docType => throw _privateConstructorUsedError;
  String? get typeName => throw _privateConstructorUsedError;
  int? get category => throw _privateConstructorUsedError;
  String? get cateName => throw _privateConstructorUsedError;
  String? get cateColor => throw _privateConstructorUsedError;
  int? get lawsuit => throw _privateConstructorUsedError;
  String? get lawsuitName => throw _privateConstructorUsedError;
  String get title => throw _privateConstructorUsedError;
  String? get executionDate => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  int get hit => throw _privateConstructorUsedError;
  bool get isPinned => throw _privateConstructorUsedError;

  /// 보안 등급: '1'=비공개 / '2'=팀공개 / '3'=프로젝트공개(기본) / '4'=전사공개
  String get securityLevel => throw _privateConstructorUsedError;
  String? get securityLevelDesc => throw _privateConstructorUsedError;
  String? get creatorDeptName => throw _privateConstructorUsedError;
  List<int> get allowedUsers => throw _privateConstructorUsedError;
  bool get isBlind => throw _privateConstructorUsedError;
  List<DocFileModel> get files => throw _privateConstructorUsedError;
  List<DocLinkModel> get links => throw _privateConstructorUsedError;
  SimpleUserModel? get creator => throw _privateConstructorUsedError;
  SimpleUserModel? get updator => throw _privateConstructorUsedError;
  String? get created => throw _privateConstructorUsedError;
  String? get updated => throw _privateConstructorUsedError;
  bool get isNew => throw _privateConstructorUsedError;

  /// Serializes this DocumentModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of DocumentModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $DocumentModelCopyWith<DocumentModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $DocumentModelCopyWith<$Res> {
  factory $DocumentModelCopyWith(
    DocumentModel value,
    $Res Function(DocumentModel) then,
  ) = _$DocumentModelCopyWithImpl<$Res, DocumentModel>;
  @useResult
  $Res call({
    int pk,
    SimpleProjectModel? project,
    String? projType,
    String? docType,
    String? typeName,
    int? category,
    String? cateName,
    String? cateColor,
    int? lawsuit,
    String? lawsuitName,
    String title,
    String? executionDate,
    String description,
    int hit,
    bool isPinned,
    String securityLevel,
    String? securityLevelDesc,
    String? creatorDeptName,
    List<int> allowedUsers,
    bool isBlind,
    List<DocFileModel> files,
    List<DocLinkModel> links,
    SimpleUserModel? creator,
    SimpleUserModel? updator,
    String? created,
    String? updated,
    bool isNew,
  });

  $SimpleProjectModelCopyWith<$Res>? get project;
  $SimpleUserModelCopyWith<$Res>? get creator;
  $SimpleUserModelCopyWith<$Res>? get updator;
}

/// @nodoc
class _$DocumentModelCopyWithImpl<$Res, $Val extends DocumentModel>
    implements $DocumentModelCopyWith<$Res> {
  _$DocumentModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of DocumentModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? project = freezed,
    Object? projType = freezed,
    Object? docType = freezed,
    Object? typeName = freezed,
    Object? category = freezed,
    Object? cateName = freezed,
    Object? cateColor = freezed,
    Object? lawsuit = freezed,
    Object? lawsuitName = freezed,
    Object? title = null,
    Object? executionDate = freezed,
    Object? description = null,
    Object? hit = null,
    Object? isPinned = null,
    Object? securityLevel = null,
    Object? securityLevelDesc = freezed,
    Object? creatorDeptName = freezed,
    Object? allowedUsers = null,
    Object? isBlind = null,
    Object? files = null,
    Object? links = null,
    Object? creator = freezed,
    Object? updator = freezed,
    Object? created = freezed,
    Object? updated = freezed,
    Object? isNew = null,
  }) {
    return _then(
      _value.copyWith(
            pk: null == pk
                ? _value.pk
                : pk // ignore: cast_nullable_to_non_nullable
                      as int,
            project: freezed == project
                ? _value.project
                : project // ignore: cast_nullable_to_non_nullable
                      as SimpleProjectModel?,
            projType: freezed == projType
                ? _value.projType
                : projType // ignore: cast_nullable_to_non_nullable
                      as String?,
            docType: freezed == docType
                ? _value.docType
                : docType // ignore: cast_nullable_to_non_nullable
                      as String?,
            typeName: freezed == typeName
                ? _value.typeName
                : typeName // ignore: cast_nullable_to_non_nullable
                      as String?,
            category: freezed == category
                ? _value.category
                : category // ignore: cast_nullable_to_non_nullable
                      as int?,
            cateName: freezed == cateName
                ? _value.cateName
                : cateName // ignore: cast_nullable_to_non_nullable
                      as String?,
            cateColor: freezed == cateColor
                ? _value.cateColor
                : cateColor // ignore: cast_nullable_to_non_nullable
                      as String?,
            lawsuit: freezed == lawsuit
                ? _value.lawsuit
                : lawsuit // ignore: cast_nullable_to_non_nullable
                      as int?,
            lawsuitName: freezed == lawsuitName
                ? _value.lawsuitName
                : lawsuitName // ignore: cast_nullable_to_non_nullable
                      as String?,
            title: null == title
                ? _value.title
                : title // ignore: cast_nullable_to_non_nullable
                      as String,
            executionDate: freezed == executionDate
                ? _value.executionDate
                : executionDate // ignore: cast_nullable_to_non_nullable
                      as String?,
            description: null == description
                ? _value.description
                : description // ignore: cast_nullable_to_non_nullable
                      as String,
            hit: null == hit
                ? _value.hit
                : hit // ignore: cast_nullable_to_non_nullable
                      as int,
            isPinned: null == isPinned
                ? _value.isPinned
                : isPinned // ignore: cast_nullable_to_non_nullable
                      as bool,
            securityLevel: null == securityLevel
                ? _value.securityLevel
                : securityLevel // ignore: cast_nullable_to_non_nullable
                      as String,
            securityLevelDesc: freezed == securityLevelDesc
                ? _value.securityLevelDesc
                : securityLevelDesc // ignore: cast_nullable_to_non_nullable
                      as String?,
            creatorDeptName: freezed == creatorDeptName
                ? _value.creatorDeptName
                : creatorDeptName // ignore: cast_nullable_to_non_nullable
                      as String?,
            allowedUsers: null == allowedUsers
                ? _value.allowedUsers
                : allowedUsers // ignore: cast_nullable_to_non_nullable
                      as List<int>,
            isBlind: null == isBlind
                ? _value.isBlind
                : isBlind // ignore: cast_nullable_to_non_nullable
                      as bool,
            files: null == files
                ? _value.files
                : files // ignore: cast_nullable_to_non_nullable
                      as List<DocFileModel>,
            links: null == links
                ? _value.links
                : links // ignore: cast_nullable_to_non_nullable
                      as List<DocLinkModel>,
            creator: freezed == creator
                ? _value.creator
                : creator // ignore: cast_nullable_to_non_nullable
                      as SimpleUserModel?,
            updator: freezed == updator
                ? _value.updator
                : updator // ignore: cast_nullable_to_non_nullable
                      as SimpleUserModel?,
            created: freezed == created
                ? _value.created
                : created // ignore: cast_nullable_to_non_nullable
                      as String?,
            updated: freezed == updated
                ? _value.updated
                : updated // ignore: cast_nullable_to_non_nullable
                      as String?,
            isNew: null == isNew
                ? _value.isNew
                : isNew // ignore: cast_nullable_to_non_nullable
                      as bool,
          )
          as $Val,
    );
  }

  /// Create a copy of DocumentModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SimpleProjectModelCopyWith<$Res>? get project {
    if (_value.project == null) {
      return null;
    }

    return $SimpleProjectModelCopyWith<$Res>(_value.project!, (value) {
      return _then(_value.copyWith(project: value) as $Val);
    });
  }

  /// Create a copy of DocumentModel
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

  /// Create a copy of DocumentModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SimpleUserModelCopyWith<$Res>? get updator {
    if (_value.updator == null) {
      return null;
    }

    return $SimpleUserModelCopyWith<$Res>(_value.updator!, (value) {
      return _then(_value.copyWith(updator: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$DocumentModelImplCopyWith<$Res>
    implements $DocumentModelCopyWith<$Res> {
  factory _$$DocumentModelImplCopyWith(
    _$DocumentModelImpl value,
    $Res Function(_$DocumentModelImpl) then,
  ) = __$$DocumentModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int pk,
    SimpleProjectModel? project,
    String? projType,
    String? docType,
    String? typeName,
    int? category,
    String? cateName,
    String? cateColor,
    int? lawsuit,
    String? lawsuitName,
    String title,
    String? executionDate,
    String description,
    int hit,
    bool isPinned,
    String securityLevel,
    String? securityLevelDesc,
    String? creatorDeptName,
    List<int> allowedUsers,
    bool isBlind,
    List<DocFileModel> files,
    List<DocLinkModel> links,
    SimpleUserModel? creator,
    SimpleUserModel? updator,
    String? created,
    String? updated,
    bool isNew,
  });

  @override
  $SimpleProjectModelCopyWith<$Res>? get project;
  @override
  $SimpleUserModelCopyWith<$Res>? get creator;
  @override
  $SimpleUserModelCopyWith<$Res>? get updator;
}

/// @nodoc
class __$$DocumentModelImplCopyWithImpl<$Res>
    extends _$DocumentModelCopyWithImpl<$Res, _$DocumentModelImpl>
    implements _$$DocumentModelImplCopyWith<$Res> {
  __$$DocumentModelImplCopyWithImpl(
    _$DocumentModelImpl _value,
    $Res Function(_$DocumentModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of DocumentModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? pk = null,
    Object? project = freezed,
    Object? projType = freezed,
    Object? docType = freezed,
    Object? typeName = freezed,
    Object? category = freezed,
    Object? cateName = freezed,
    Object? cateColor = freezed,
    Object? lawsuit = freezed,
    Object? lawsuitName = freezed,
    Object? title = null,
    Object? executionDate = freezed,
    Object? description = null,
    Object? hit = null,
    Object? isPinned = null,
    Object? securityLevel = null,
    Object? securityLevelDesc = freezed,
    Object? creatorDeptName = freezed,
    Object? allowedUsers = null,
    Object? isBlind = null,
    Object? files = null,
    Object? links = null,
    Object? creator = freezed,
    Object? updator = freezed,
    Object? created = freezed,
    Object? updated = freezed,
    Object? isNew = null,
  }) {
    return _then(
      _$DocumentModelImpl(
        pk: null == pk
            ? _value.pk
            : pk // ignore: cast_nullable_to_non_nullable
                  as int,
        project: freezed == project
            ? _value.project
            : project // ignore: cast_nullable_to_non_nullable
                  as SimpleProjectModel?,
        projType: freezed == projType
            ? _value.projType
            : projType // ignore: cast_nullable_to_non_nullable
                  as String?,
        docType: freezed == docType
            ? _value.docType
            : docType // ignore: cast_nullable_to_non_nullable
                  as String?,
        typeName: freezed == typeName
            ? _value.typeName
            : typeName // ignore: cast_nullable_to_non_nullable
                  as String?,
        category: freezed == category
            ? _value.category
            : category // ignore: cast_nullable_to_non_nullable
                  as int?,
        cateName: freezed == cateName
            ? _value.cateName
            : cateName // ignore: cast_nullable_to_non_nullable
                  as String?,
        cateColor: freezed == cateColor
            ? _value.cateColor
            : cateColor // ignore: cast_nullable_to_non_nullable
                  as String?,
        lawsuit: freezed == lawsuit
            ? _value.lawsuit
            : lawsuit // ignore: cast_nullable_to_non_nullable
                  as int?,
        lawsuitName: freezed == lawsuitName
            ? _value.lawsuitName
            : lawsuitName // ignore: cast_nullable_to_non_nullable
                  as String?,
        title: null == title
            ? _value.title
            : title // ignore: cast_nullable_to_non_nullable
                  as String,
        executionDate: freezed == executionDate
            ? _value.executionDate
            : executionDate // ignore: cast_nullable_to_non_nullable
                  as String?,
        description: null == description
            ? _value.description
            : description // ignore: cast_nullable_to_non_nullable
                  as String,
        hit: null == hit
            ? _value.hit
            : hit // ignore: cast_nullable_to_non_nullable
                  as int,
        isPinned: null == isPinned
            ? _value.isPinned
            : isPinned // ignore: cast_nullable_to_non_nullable
                  as bool,
        securityLevel: null == securityLevel
            ? _value.securityLevel
            : securityLevel // ignore: cast_nullable_to_non_nullable
                  as String,
        securityLevelDesc: freezed == securityLevelDesc
            ? _value.securityLevelDesc
            : securityLevelDesc // ignore: cast_nullable_to_non_nullable
                  as String?,
        creatorDeptName: freezed == creatorDeptName
            ? _value.creatorDeptName
            : creatorDeptName // ignore: cast_nullable_to_non_nullable
                  as String?,
        allowedUsers: null == allowedUsers
            ? _value._allowedUsers
            : allowedUsers // ignore: cast_nullable_to_non_nullable
                  as List<int>,
        isBlind: null == isBlind
            ? _value.isBlind
            : isBlind // ignore: cast_nullable_to_non_nullable
                  as bool,
        files: null == files
            ? _value._files
            : files // ignore: cast_nullable_to_non_nullable
                  as List<DocFileModel>,
        links: null == links
            ? _value._links
            : links // ignore: cast_nullable_to_non_nullable
                  as List<DocLinkModel>,
        creator: freezed == creator
            ? _value.creator
            : creator // ignore: cast_nullable_to_non_nullable
                  as SimpleUserModel?,
        updator: freezed == updator
            ? _value.updator
            : updator // ignore: cast_nullable_to_non_nullable
                  as SimpleUserModel?,
        created: freezed == created
            ? _value.created
            : created // ignore: cast_nullable_to_non_nullable
                  as String?,
        updated: freezed == updated
            ? _value.updated
            : updated // ignore: cast_nullable_to_non_nullable
                  as String?,
        isNew: null == isNew
            ? _value.isNew
            : isNew // ignore: cast_nullable_to_non_nullable
                  as bool,
      ),
    );
  }
}

/// @nodoc
@JsonSerializable()
class _$DocumentModelImpl implements _DocumentModel {
  const _$DocumentModelImpl({
    required this.pk,
    this.project,
    this.projType,
    this.docType,
    this.typeName,
    this.category,
    this.cateName,
    this.cateColor,
    this.lawsuit,
    this.lawsuitName,
    required this.title,
    this.executionDate,
    this.description = '',
    this.hit = 0,
    this.isPinned = false,
    this.securityLevel = '3',
    this.securityLevelDesc,
    this.creatorDeptName,
    final List<int> allowedUsers = const [],
    this.isBlind = false,
    final List<DocFileModel> files = const [],
    final List<DocLinkModel> links = const [],
    this.creator,
    this.updator,
    this.created,
    this.updated,
    this.isNew = false,
  }) : _allowedUsers = allowedUsers,
       _files = files,
       _links = links;

  factory _$DocumentModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$DocumentModelImplFromJson(json);

  @override
  final int pk;
  @override
  final SimpleProjectModel? project;
  @override
  final String? projType;
  @override
  final String? docType;
  @override
  final String? typeName;
  @override
  final int? category;
  @override
  final String? cateName;
  @override
  final String? cateColor;
  @override
  final int? lawsuit;
  @override
  final String? lawsuitName;
  @override
  final String title;
  @override
  final String? executionDate;
  @override
  @JsonKey()
  final String description;
  @override
  @JsonKey()
  final int hit;
  @override
  @JsonKey()
  final bool isPinned;

  /// 보안 등급: '1'=비공개 / '2'=팀공개 / '3'=프로젝트공개(기본) / '4'=전사공개
  @override
  @JsonKey()
  final String securityLevel;
  @override
  final String? securityLevelDesc;
  @override
  final String? creatorDeptName;
  final List<int> _allowedUsers;
  @override
  @JsonKey()
  List<int> get allowedUsers {
    if (_allowedUsers is EqualUnmodifiableListView) return _allowedUsers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_allowedUsers);
  }

  @override
  @JsonKey()
  final bool isBlind;
  final List<DocFileModel> _files;
  @override
  @JsonKey()
  List<DocFileModel> get files {
    if (_files is EqualUnmodifiableListView) return _files;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_files);
  }

  final List<DocLinkModel> _links;
  @override
  @JsonKey()
  List<DocLinkModel> get links {
    if (_links is EqualUnmodifiableListView) return _links;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_links);
  }

  @override
  final SimpleUserModel? creator;
  @override
  final SimpleUserModel? updator;
  @override
  final String? created;
  @override
  final String? updated;
  @override
  @JsonKey()
  final bool isNew;

  @override
  String toString() {
    return 'DocumentModel(pk: $pk, project: $project, projType: $projType, docType: $docType, typeName: $typeName, category: $category, cateName: $cateName, cateColor: $cateColor, lawsuit: $lawsuit, lawsuitName: $lawsuitName, title: $title, executionDate: $executionDate, description: $description, hit: $hit, isPinned: $isPinned, securityLevel: $securityLevel, securityLevelDesc: $securityLevelDesc, creatorDeptName: $creatorDeptName, allowedUsers: $allowedUsers, isBlind: $isBlind, files: $files, links: $links, creator: $creator, updator: $updator, created: $created, updated: $updated, isNew: $isNew)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$DocumentModelImpl &&
            (identical(other.pk, pk) || other.pk == pk) &&
            (identical(other.project, project) || other.project == project) &&
            (identical(other.projType, projType) ||
                other.projType == projType) &&
            (identical(other.docType, docType) || other.docType == docType) &&
            (identical(other.typeName, typeName) ||
                other.typeName == typeName) &&
            (identical(other.category, category) ||
                other.category == category) &&
            (identical(other.cateName, cateName) ||
                other.cateName == cateName) &&
            (identical(other.cateColor, cateColor) ||
                other.cateColor == cateColor) &&
            (identical(other.lawsuit, lawsuit) || other.lawsuit == lawsuit) &&
            (identical(other.lawsuitName, lawsuitName) ||
                other.lawsuitName == lawsuitName) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.executionDate, executionDate) ||
                other.executionDate == executionDate) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.hit, hit) || other.hit == hit) &&
            (identical(other.isPinned, isPinned) ||
                other.isPinned == isPinned) &&
            (identical(other.securityLevel, securityLevel) ||
                other.securityLevel == securityLevel) &&
            (identical(other.securityLevelDesc, securityLevelDesc) ||
                other.securityLevelDesc == securityLevelDesc) &&
            (identical(other.creatorDeptName, creatorDeptName) ||
                other.creatorDeptName == creatorDeptName) &&
            const DeepCollectionEquality().equals(
              other._allowedUsers,
              _allowedUsers,
            ) &&
            (identical(other.isBlind, isBlind) || other.isBlind == isBlind) &&
            const DeepCollectionEquality().equals(other._files, _files) &&
            const DeepCollectionEquality().equals(other._links, _links) &&
            (identical(other.creator, creator) || other.creator == creator) &&
            (identical(other.updator, updator) || other.updator == updator) &&
            (identical(other.created, created) || other.created == created) &&
            (identical(other.updated, updated) || other.updated == updated) &&
            (identical(other.isNew, isNew) || other.isNew == isNew));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hashAll([
    runtimeType,
    pk,
    project,
    projType,
    docType,
    typeName,
    category,
    cateName,
    cateColor,
    lawsuit,
    lawsuitName,
    title,
    executionDate,
    description,
    hit,
    isPinned,
    securityLevel,
    securityLevelDesc,
    creatorDeptName,
    const DeepCollectionEquality().hash(_allowedUsers),
    isBlind,
    const DeepCollectionEquality().hash(_files),
    const DeepCollectionEquality().hash(_links),
    creator,
    updator,
    created,
    updated,
    isNew,
  ]);

  /// Create a copy of DocumentModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$DocumentModelImplCopyWith<_$DocumentModelImpl> get copyWith =>
      __$$DocumentModelImplCopyWithImpl<_$DocumentModelImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$DocumentModelImplToJson(this);
  }
}

abstract class _DocumentModel implements DocumentModel {
  const factory _DocumentModel({
    required final int pk,
    final SimpleProjectModel? project,
    final String? projType,
    final String? docType,
    final String? typeName,
    final int? category,
    final String? cateName,
    final String? cateColor,
    final int? lawsuit,
    final String? lawsuitName,
    required final String title,
    final String? executionDate,
    final String description,
    final int hit,
    final bool isPinned,
    final String securityLevel,
    final String? securityLevelDesc,
    final String? creatorDeptName,
    final List<int> allowedUsers,
    final bool isBlind,
    final List<DocFileModel> files,
    final List<DocLinkModel> links,
    final SimpleUserModel? creator,
    final SimpleUserModel? updator,
    final String? created,
    final String? updated,
    final bool isNew,
  }) = _$DocumentModelImpl;

  factory _DocumentModel.fromJson(Map<String, dynamic> json) =
      _$DocumentModelImpl.fromJson;

  @override
  int get pk;
  @override
  SimpleProjectModel? get project;
  @override
  String? get projType;
  @override
  String? get docType;
  @override
  String? get typeName;
  @override
  int? get category;
  @override
  String? get cateName;
  @override
  String? get cateColor;
  @override
  int? get lawsuit;
  @override
  String? get lawsuitName;
  @override
  String get title;
  @override
  String? get executionDate;
  @override
  String get description;
  @override
  int get hit;
  @override
  bool get isPinned;

  /// 보안 등급: '1'=비공개 / '2'=팀공개 / '3'=프로젝트공개(기본) / '4'=전사공개
  @override
  String get securityLevel;
  @override
  String? get securityLevelDesc;
  @override
  String? get creatorDeptName;
  @override
  List<int> get allowedUsers;
  @override
  bool get isBlind;
  @override
  List<DocFileModel> get files;
  @override
  List<DocLinkModel> get links;
  @override
  SimpleUserModel? get creator;
  @override
  SimpleUserModel? get updator;
  @override
  String? get created;
  @override
  String? get updated;
  @override
  bool get isNew;

  /// Create a copy of DocumentModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$DocumentModelImplCopyWith<_$DocumentModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

DocumentListResponseModel _$DocumentListResponseModelFromJson(
  Map<String, dynamic> json,
) {
  return _DocumentListResponseModel.fromJson(json);
}

/// @nodoc
mixin _$DocumentListResponseModel {
  int get count => throw _privateConstructorUsedError;
  String? get next => throw _privateConstructorUsedError;
  String? get previous => throw _privateConstructorUsedError;
  List<DocumentModel> get results => throw _privateConstructorUsedError;

  /// Serializes this DocumentListResponseModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of DocumentListResponseModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $DocumentListResponseModelCopyWith<DocumentListResponseModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $DocumentListResponseModelCopyWith<$Res> {
  factory $DocumentListResponseModelCopyWith(
    DocumentListResponseModel value,
    $Res Function(DocumentListResponseModel) then,
  ) = _$DocumentListResponseModelCopyWithImpl<$Res, DocumentListResponseModel>;
  @useResult
  $Res call({
    int count,
    String? next,
    String? previous,
    List<DocumentModel> results,
  });
}

/// @nodoc
class _$DocumentListResponseModelCopyWithImpl<
  $Res,
  $Val extends DocumentListResponseModel
>
    implements $DocumentListResponseModelCopyWith<$Res> {
  _$DocumentListResponseModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of DocumentListResponseModel
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
                      as List<DocumentModel>,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$DocumentListResponseModelImplCopyWith<$Res>
    implements $DocumentListResponseModelCopyWith<$Res> {
  factory _$$DocumentListResponseModelImplCopyWith(
    _$DocumentListResponseModelImpl value,
    $Res Function(_$DocumentListResponseModelImpl) then,
  ) = __$$DocumentListResponseModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int count,
    String? next,
    String? previous,
    List<DocumentModel> results,
  });
}

/// @nodoc
class __$$DocumentListResponseModelImplCopyWithImpl<$Res>
    extends
        _$DocumentListResponseModelCopyWithImpl<
          $Res,
          _$DocumentListResponseModelImpl
        >
    implements _$$DocumentListResponseModelImplCopyWith<$Res> {
  __$$DocumentListResponseModelImplCopyWithImpl(
    _$DocumentListResponseModelImpl _value,
    $Res Function(_$DocumentListResponseModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of DocumentListResponseModel
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
      _$DocumentListResponseModelImpl(
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
                  as List<DocumentModel>,
      ),
    );
  }
}

/// @nodoc
@JsonSerializable()
class _$DocumentListResponseModelImpl implements _DocumentListResponseModel {
  const _$DocumentListResponseModelImpl({
    required this.count,
    this.next,
    this.previous,
    required final List<DocumentModel> results,
  }) : _results = results;

  factory _$DocumentListResponseModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$DocumentListResponseModelImplFromJson(json);

  @override
  final int count;
  @override
  final String? next;
  @override
  final String? previous;
  final List<DocumentModel> _results;
  @override
  List<DocumentModel> get results {
    if (_results is EqualUnmodifiableListView) return _results;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_results);
  }

  @override
  String toString() {
    return 'DocumentListResponseModel(count: $count, next: $next, previous: $previous, results: $results)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$DocumentListResponseModelImpl &&
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

  /// Create a copy of DocumentListResponseModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$DocumentListResponseModelImplCopyWith<_$DocumentListResponseModelImpl>
  get copyWith =>
      __$$DocumentListResponseModelImplCopyWithImpl<
        _$DocumentListResponseModelImpl
      >(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$DocumentListResponseModelImplToJson(this);
  }
}

abstract class _DocumentListResponseModel implements DocumentListResponseModel {
  const factory _DocumentListResponseModel({
    required final int count,
    final String? next,
    final String? previous,
    required final List<DocumentModel> results,
  }) = _$DocumentListResponseModelImpl;

  factory _DocumentListResponseModel.fromJson(Map<String, dynamic> json) =
      _$DocumentListResponseModelImpl.fromJson;

  @override
  int get count;
  @override
  String? get next;
  @override
  String? get previous;
  @override
  List<DocumentModel> get results;

  /// Create a copy of DocumentListResponseModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$DocumentListResponseModelImplCopyWith<_$DocumentListResponseModelImpl>
  get copyWith => throw _privateConstructorUsedError;
}
