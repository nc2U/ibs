// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'approval_model.dart';

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
  @JsonKey(readValue: _readId)
  int get id => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get name => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get code => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  int get order => throw _privateConstructorUsedError;
  bool get isActive => throw _privateConstructorUsedError;

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
    @JsonKey(readValue: _readId) int id,
    @JsonKey(readValue: _readStr) String name,
    @JsonKey(readValue: _readStr) String code,
    String description,
    int order,
    bool isActive,
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
    Object? id = null,
    Object? name = null,
    Object? code = null,
    Object? description = null,
    Object? order = null,
    Object? isActive = null,
  }) {
    return _then(
      _value.copyWith(
            id: null == id
                ? _value.id
                : id // ignore: cast_nullable_to_non_nullable
                      as int,
            name: null == name
                ? _value.name
                : name // ignore: cast_nullable_to_non_nullable
                      as String,
            code: null == code
                ? _value.code
                : code // ignore: cast_nullable_to_non_nullable
                      as String,
            description: null == description
                ? _value.description
                : description // ignore: cast_nullable_to_non_nullable
                      as String,
            order: null == order
                ? _value.order
                : order // ignore: cast_nullable_to_non_nullable
                      as int,
            isActive: null == isActive
                ? _value.isActive
                : isActive // ignore: cast_nullable_to_non_nullable
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
    @JsonKey(readValue: _readId) int id,
    @JsonKey(readValue: _readStr) String name,
    @JsonKey(readValue: _readStr) String code,
    String description,
    int order,
    bool isActive,
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
    Object? id = null,
    Object? name = null,
    Object? code = null,
    Object? description = null,
    Object? order = null,
    Object? isActive = null,
  }) {
    return _then(
      _$DocCategoryModelImpl(
        id: null == id
            ? _value.id
            : id // ignore: cast_nullable_to_non_nullable
                  as int,
        name: null == name
            ? _value.name
            : name // ignore: cast_nullable_to_non_nullable
                  as String,
        code: null == code
            ? _value.code
            : code // ignore: cast_nullable_to_non_nullable
                  as String,
        description: null == description
            ? _value.description
            : description // ignore: cast_nullable_to_non_nullable
                  as String,
        order: null == order
            ? _value.order
            : order // ignore: cast_nullable_to_non_nullable
                  as int,
        isActive: null == isActive
            ? _value.isActive
            : isActive // ignore: cast_nullable_to_non_nullable
                  as bool,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$DocCategoryModelImpl implements _DocCategoryModel {
  const _$DocCategoryModelImpl({
    @JsonKey(readValue: _readId) required this.id,
    @JsonKey(readValue: _readStr) this.name = '',
    @JsonKey(readValue: _readStr) this.code = '',
    this.description = '',
    this.order = 1,
    this.isActive = true,
  });

  factory _$DocCategoryModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$DocCategoryModelImplFromJson(json);

  @override
  @JsonKey(readValue: _readId)
  final int id;
  @override
  @JsonKey(readValue: _readStr)
  final String name;
  @override
  @JsonKey(readValue: _readStr)
  final String code;
  @override
  @JsonKey()
  final String description;
  @override
  @JsonKey()
  final int order;
  @override
  @JsonKey()
  final bool isActive;

  @override
  String toString() {
    return 'DocCategoryModel(id: $id, name: $name, code: $code, description: $description, order: $order, isActive: $isActive)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$DocCategoryModelImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.code, code) || other.code == code) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.order, order) || other.order == order) &&
            (identical(other.isActive, isActive) ||
                other.isActive == isActive));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, id, name, code, description, order, isActive);

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
    @JsonKey(readValue: _readId) required final int id,
    @JsonKey(readValue: _readStr) final String name,
    @JsonKey(readValue: _readStr) final String code,
    final String description,
    final int order,
    final bool isActive,
  }) = _$DocCategoryModelImpl;

  factory _DocCategoryModel.fromJson(Map<String, dynamic> json) =
      _$DocCategoryModelImpl.fromJson;

  @override
  @JsonKey(readValue: _readId)
  int get id;
  @override
  @JsonKey(readValue: _readStr)
  String get name;
  @override
  @JsonKey(readValue: _readStr)
  String get code;
  @override
  String get description;
  @override
  int get order;
  @override
  bool get isActive;

  /// Create a copy of DocCategoryModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$DocCategoryModelImplCopyWith<_$DocCategoryModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

FormFieldModel _$FormFieldModelFromJson(Map<String, dynamic> json) {
  return _FormFieldModel.fromJson(json);
}

/// @nodoc
mixin _$FormFieldModel {
  String get key => throw _privateConstructorUsedError;
  String get label => throw _privateConstructorUsedError;
  String get type =>
      throw _privateConstructorUsedError; // text, textarea, number, date, select
  bool get required => throw _privateConstructorUsedError;
  List<String>? get options => throw _privateConstructorUsedError;

  /// Serializes this FormFieldModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of FormFieldModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $FormFieldModelCopyWith<FormFieldModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $FormFieldModelCopyWith<$Res> {
  factory $FormFieldModelCopyWith(
    FormFieldModel value,
    $Res Function(FormFieldModel) then,
  ) = _$FormFieldModelCopyWithImpl<$Res, FormFieldModel>;
  @useResult
  $Res call({
    String key,
    String label,
    String type,
    bool required,
    List<String>? options,
  });
}

/// @nodoc
class _$FormFieldModelCopyWithImpl<$Res, $Val extends FormFieldModel>
    implements $FormFieldModelCopyWith<$Res> {
  _$FormFieldModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of FormFieldModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? key = null,
    Object? label = null,
    Object? type = null,
    Object? required = null,
    Object? options = freezed,
  }) {
    return _then(
      _value.copyWith(
            key: null == key
                ? _value.key
                : key // ignore: cast_nullable_to_non_nullable
                      as String,
            label: null == label
                ? _value.label
                : label // ignore: cast_nullable_to_non_nullable
                      as String,
            type: null == type
                ? _value.type
                : type // ignore: cast_nullable_to_non_nullable
                      as String,
            required: null == required
                ? _value.required
                : required // ignore: cast_nullable_to_non_nullable
                      as bool,
            options: freezed == options
                ? _value.options
                : options // ignore: cast_nullable_to_non_nullable
                      as List<String>?,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$FormFieldModelImplCopyWith<$Res>
    implements $FormFieldModelCopyWith<$Res> {
  factory _$$FormFieldModelImplCopyWith(
    _$FormFieldModelImpl value,
    $Res Function(_$FormFieldModelImpl) then,
  ) = __$$FormFieldModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    String key,
    String label,
    String type,
    bool required,
    List<String>? options,
  });
}

/// @nodoc
class __$$FormFieldModelImplCopyWithImpl<$Res>
    extends _$FormFieldModelCopyWithImpl<$Res, _$FormFieldModelImpl>
    implements _$$FormFieldModelImplCopyWith<$Res> {
  __$$FormFieldModelImplCopyWithImpl(
    _$FormFieldModelImpl _value,
    $Res Function(_$FormFieldModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of FormFieldModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? key = null,
    Object? label = null,
    Object? type = null,
    Object? required = null,
    Object? options = freezed,
  }) {
    return _then(
      _$FormFieldModelImpl(
        key: null == key
            ? _value.key
            : key // ignore: cast_nullable_to_non_nullable
                  as String,
        label: null == label
            ? _value.label
            : label // ignore: cast_nullable_to_non_nullable
                  as String,
        type: null == type
            ? _value.type
            : type // ignore: cast_nullable_to_non_nullable
                  as String,
        required: null == required
            ? _value.required
            : required // ignore: cast_nullable_to_non_nullable
                  as bool,
        options: freezed == options
            ? _value._options
            : options // ignore: cast_nullable_to_non_nullable
                  as List<String>?,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$FormFieldModelImpl implements _FormFieldModel {
  const _$FormFieldModelImpl({
    required this.key,
    required this.label,
    required this.type,
    this.required = false,
    final List<String>? options,
  }) : _options = options;

  factory _$FormFieldModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$FormFieldModelImplFromJson(json);

  @override
  final String key;
  @override
  final String label;
  @override
  final String type;
  // text, textarea, number, date, select
  @override
  @JsonKey()
  final bool required;
  final List<String>? _options;
  @override
  List<String>? get options {
    final value = _options;
    if (value == null) return null;
    if (_options is EqualUnmodifiableListView) return _options;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  @override
  String toString() {
    return 'FormFieldModel(key: $key, label: $label, type: $type, required: $required, options: $options)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$FormFieldModelImpl &&
            (identical(other.key, key) || other.key == key) &&
            (identical(other.label, label) || other.label == label) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.required, required) ||
                other.required == required) &&
            const DeepCollectionEquality().equals(other._options, _options));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
    runtimeType,
    key,
    label,
    type,
    required,
    const DeepCollectionEquality().hash(_options),
  );

  /// Create a copy of FormFieldModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$FormFieldModelImplCopyWith<_$FormFieldModelImpl> get copyWith =>
      __$$FormFieldModelImplCopyWithImpl<_$FormFieldModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$FormFieldModelImplToJson(this);
  }
}

abstract class _FormFieldModel implements FormFieldModel {
  const factory _FormFieldModel({
    required final String key,
    required final String label,
    required final String type,
    final bool required,
    final List<String>? options,
  }) = _$FormFieldModelImpl;

  factory _FormFieldModel.fromJson(Map<String, dynamic> json) =
      _$FormFieldModelImpl.fromJson;

  @override
  String get key;
  @override
  String get label;
  @override
  String get type; // text, textarea, number, date, select
  @override
  bool get required;
  @override
  List<String>? get options;

  /// Create a copy of FormFieldModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$FormFieldModelImplCopyWith<_$FormFieldModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

DocumentTypeModel _$DocumentTypeModelFromJson(Map<String, dynamic> json) {
  return _DocumentTypeModel.fromJson(json);
}

/// @nodoc
mixin _$DocumentTypeModel {
  @JsonKey(readValue: _readId)
  int get id => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get name => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get code => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  String get formTemplateKey => throw _privateConstructorUsedError;
  String get routeType => throw _privateConstructorUsedError;
  int? get category => throw _privateConstructorUsedError;
  String? get categoryName => throw _privateConstructorUsedError;
  bool get isActive => throw _privateConstructorUsedError;

  /// Serializes this DocumentTypeModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of DocumentTypeModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $DocumentTypeModelCopyWith<DocumentTypeModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $DocumentTypeModelCopyWith<$Res> {
  factory $DocumentTypeModelCopyWith(
    DocumentTypeModel value,
    $Res Function(DocumentTypeModel) then,
  ) = _$DocumentTypeModelCopyWithImpl<$Res, DocumentTypeModel>;
  @useResult
  $Res call({
    @JsonKey(readValue: _readId) int id,
    @JsonKey(readValue: _readStr) String name,
    @JsonKey(readValue: _readStr) String code,
    String description,
    String formTemplateKey,
    String routeType,
    int? category,
    String? categoryName,
    bool isActive,
  });
}

/// @nodoc
class _$DocumentTypeModelCopyWithImpl<$Res, $Val extends DocumentTypeModel>
    implements $DocumentTypeModelCopyWith<$Res> {
  _$DocumentTypeModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of DocumentTypeModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? name = null,
    Object? code = null,
    Object? description = null,
    Object? formTemplateKey = null,
    Object? routeType = null,
    Object? category = freezed,
    Object? categoryName = freezed,
    Object? isActive = null,
  }) {
    return _then(
      _value.copyWith(
            id: null == id
                ? _value.id
                : id // ignore: cast_nullable_to_non_nullable
                      as int,
            name: null == name
                ? _value.name
                : name // ignore: cast_nullable_to_non_nullable
                      as String,
            code: null == code
                ? _value.code
                : code // ignore: cast_nullable_to_non_nullable
                      as String,
            description: null == description
                ? _value.description
                : description // ignore: cast_nullable_to_non_nullable
                      as String,
            formTemplateKey: null == formTemplateKey
                ? _value.formTemplateKey
                : formTemplateKey // ignore: cast_nullable_to_non_nullable
                      as String,
            routeType: null == routeType
                ? _value.routeType
                : routeType // ignore: cast_nullable_to_non_nullable
                      as String,
            category: freezed == category
                ? _value.category
                : category // ignore: cast_nullable_to_non_nullable
                      as int?,
            categoryName: freezed == categoryName
                ? _value.categoryName
                : categoryName // ignore: cast_nullable_to_non_nullable
                      as String?,
            isActive: null == isActive
                ? _value.isActive
                : isActive // ignore: cast_nullable_to_non_nullable
                      as bool,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$DocumentTypeModelImplCopyWith<$Res>
    implements $DocumentTypeModelCopyWith<$Res> {
  factory _$$DocumentTypeModelImplCopyWith(
    _$DocumentTypeModelImpl value,
    $Res Function(_$DocumentTypeModelImpl) then,
  ) = __$$DocumentTypeModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    @JsonKey(readValue: _readId) int id,
    @JsonKey(readValue: _readStr) String name,
    @JsonKey(readValue: _readStr) String code,
    String description,
    String formTemplateKey,
    String routeType,
    int? category,
    String? categoryName,
    bool isActive,
  });
}

/// @nodoc
class __$$DocumentTypeModelImplCopyWithImpl<$Res>
    extends _$DocumentTypeModelCopyWithImpl<$Res, _$DocumentTypeModelImpl>
    implements _$$DocumentTypeModelImplCopyWith<$Res> {
  __$$DocumentTypeModelImplCopyWithImpl(
    _$DocumentTypeModelImpl _value,
    $Res Function(_$DocumentTypeModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of DocumentTypeModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? name = null,
    Object? code = null,
    Object? description = null,
    Object? formTemplateKey = null,
    Object? routeType = null,
    Object? category = freezed,
    Object? categoryName = freezed,
    Object? isActive = null,
  }) {
    return _then(
      _$DocumentTypeModelImpl(
        id: null == id
            ? _value.id
            : id // ignore: cast_nullable_to_non_nullable
                  as int,
        name: null == name
            ? _value.name
            : name // ignore: cast_nullable_to_non_nullable
                  as String,
        code: null == code
            ? _value.code
            : code // ignore: cast_nullable_to_non_nullable
                  as String,
        description: null == description
            ? _value.description
            : description // ignore: cast_nullable_to_non_nullable
                  as String,
        formTemplateKey: null == formTemplateKey
            ? _value.formTemplateKey
            : formTemplateKey // ignore: cast_nullable_to_non_nullable
                  as String,
        routeType: null == routeType
            ? _value.routeType
            : routeType // ignore: cast_nullable_to_non_nullable
                  as String,
        category: freezed == category
            ? _value.category
            : category // ignore: cast_nullable_to_non_nullable
                  as int?,
        categoryName: freezed == categoryName
            ? _value.categoryName
            : categoryName // ignore: cast_nullable_to_non_nullable
                  as String?,
        isActive: null == isActive
            ? _value.isActive
            : isActive // ignore: cast_nullable_to_non_nullable
                  as bool,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$DocumentTypeModelImpl implements _DocumentTypeModel {
  const _$DocumentTypeModelImpl({
    @JsonKey(readValue: _readId) required this.id,
    @JsonKey(readValue: _readStr) this.name = '',
    @JsonKey(readValue: _readStr) this.code = '',
    this.description = '',
    this.formTemplateKey = 'GENERAL',
    this.routeType = 'organization',
    this.category,
    this.categoryName,
    this.isActive = true,
  });

  factory _$DocumentTypeModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$DocumentTypeModelImplFromJson(json);

  @override
  @JsonKey(readValue: _readId)
  final int id;
  @override
  @JsonKey(readValue: _readStr)
  final String name;
  @override
  @JsonKey(readValue: _readStr)
  final String code;
  @override
  @JsonKey()
  final String description;
  @override
  @JsonKey()
  final String formTemplateKey;
  @override
  @JsonKey()
  final String routeType;
  @override
  final int? category;
  @override
  final String? categoryName;
  @override
  @JsonKey()
  final bool isActive;

  @override
  String toString() {
    return 'DocumentTypeModel(id: $id, name: $name, code: $code, description: $description, formTemplateKey: $formTemplateKey, routeType: $routeType, category: $category, categoryName: $categoryName, isActive: $isActive)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$DocumentTypeModelImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.code, code) || other.code == code) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.formTemplateKey, formTemplateKey) ||
                other.formTemplateKey == formTemplateKey) &&
            (identical(other.routeType, routeType) ||
                other.routeType == routeType) &&
            (identical(other.category, category) ||
                other.category == category) &&
            (identical(other.categoryName, categoryName) ||
                other.categoryName == categoryName) &&
            (identical(other.isActive, isActive) ||
                other.isActive == isActive));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
    runtimeType,
    id,
    name,
    code,
    description,
    formTemplateKey,
    routeType,
    category,
    categoryName,
    isActive,
  );

  /// Create a copy of DocumentTypeModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$DocumentTypeModelImplCopyWith<_$DocumentTypeModelImpl> get copyWith =>
      __$$DocumentTypeModelImplCopyWithImpl<_$DocumentTypeModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$DocumentTypeModelImplToJson(this);
  }
}

abstract class _DocumentTypeModel implements DocumentTypeModel {
  const factory _DocumentTypeModel({
    @JsonKey(readValue: _readId) required final int id,
    @JsonKey(readValue: _readStr) final String name,
    @JsonKey(readValue: _readStr) final String code,
    final String description,
    final String formTemplateKey,
    final String routeType,
    final int? category,
    final String? categoryName,
    final bool isActive,
  }) = _$DocumentTypeModelImpl;

  factory _DocumentTypeModel.fromJson(Map<String, dynamic> json) =
      _$DocumentTypeModelImpl.fromJson;

  @override
  @JsonKey(readValue: _readId)
  int get id;
  @override
  @JsonKey(readValue: _readStr)
  String get name;
  @override
  @JsonKey(readValue: _readStr)
  String get code;
  @override
  String get description;
  @override
  String get formTemplateKey;
  @override
  String get routeType;
  @override
  int? get category;
  @override
  String? get categoryName;
  @override
  bool get isActive;

  /// Create a copy of DocumentTypeModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$DocumentTypeModelImplCopyWith<_$DocumentTypeModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

StaffAssignmentItemModel _$StaffAssignmentItemModelFromJson(
  Map<String, dynamic> json,
) {
  return _StaffAssignmentItemModel.fromJson(json);
}

/// @nodoc
mixin _$StaffAssignmentItemModel {
  @JsonKey(readValue: _readId)
  int get id => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readCompanyId)
  int? get company => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readCompanyName)
  String? get companyName => throw _privateConstructorUsedError;
  int? get department => throw _privateConstructorUsedError;
  String? get departmentName => throw _privateConstructorUsedError;
  int? get duty => throw _privateConstructorUsedError;
  String? get dutyName => throw _privateConstructorUsedError;
  int? get position => throw _privateConstructorUsedError;
  String? get positionName => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readDesc)
  String? get assignedTasks => throw _privateConstructorUsedError;
  bool get isPrimary => throw _privateConstructorUsedError;

  /// Serializes this StaffAssignmentItemModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of StaffAssignmentItemModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $StaffAssignmentItemModelCopyWith<StaffAssignmentItemModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $StaffAssignmentItemModelCopyWith<$Res> {
  factory $StaffAssignmentItemModelCopyWith(
    StaffAssignmentItemModel value,
    $Res Function(StaffAssignmentItemModel) then,
  ) = _$StaffAssignmentItemModelCopyWithImpl<$Res, StaffAssignmentItemModel>;
  @useResult
  $Res call({
    @JsonKey(readValue: _readId) int id,
    @JsonKey(readValue: _readCompanyId) int? company,
    @JsonKey(readValue: _readCompanyName) String? companyName,
    int? department,
    String? departmentName,
    int? duty,
    String? dutyName,
    int? position,
    String? positionName,
    @JsonKey(readValue: _readDesc) String? assignedTasks,
    bool isPrimary,
  });
}

/// @nodoc
class _$StaffAssignmentItemModelCopyWithImpl<
  $Res,
  $Val extends StaffAssignmentItemModel
>
    implements $StaffAssignmentItemModelCopyWith<$Res> {
  _$StaffAssignmentItemModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of StaffAssignmentItemModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? company = freezed,
    Object? companyName = freezed,
    Object? department = freezed,
    Object? departmentName = freezed,
    Object? duty = freezed,
    Object? dutyName = freezed,
    Object? position = freezed,
    Object? positionName = freezed,
    Object? assignedTasks = freezed,
    Object? isPrimary = null,
  }) {
    return _then(
      _value.copyWith(
            id: null == id
                ? _value.id
                : id // ignore: cast_nullable_to_non_nullable
                      as int,
            company: freezed == company
                ? _value.company
                : company // ignore: cast_nullable_to_non_nullable
                      as int?,
            companyName: freezed == companyName
                ? _value.companyName
                : companyName // ignore: cast_nullable_to_non_nullable
                      as String?,
            department: freezed == department
                ? _value.department
                : department // ignore: cast_nullable_to_non_nullable
                      as int?,
            departmentName: freezed == departmentName
                ? _value.departmentName
                : departmentName // ignore: cast_nullable_to_non_nullable
                      as String?,
            duty: freezed == duty
                ? _value.duty
                : duty // ignore: cast_nullable_to_non_nullable
                      as int?,
            dutyName: freezed == dutyName
                ? _value.dutyName
                : dutyName // ignore: cast_nullable_to_non_nullable
                      as String?,
            position: freezed == position
                ? _value.position
                : position // ignore: cast_nullable_to_non_nullable
                      as int?,
            positionName: freezed == positionName
                ? _value.positionName
                : positionName // ignore: cast_nullable_to_non_nullable
                      as String?,
            assignedTasks: freezed == assignedTasks
                ? _value.assignedTasks
                : assignedTasks // ignore: cast_nullable_to_non_nullable
                      as String?,
            isPrimary: null == isPrimary
                ? _value.isPrimary
                : isPrimary // ignore: cast_nullable_to_non_nullable
                      as bool,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$StaffAssignmentItemModelImplCopyWith<$Res>
    implements $StaffAssignmentItemModelCopyWith<$Res> {
  factory _$$StaffAssignmentItemModelImplCopyWith(
    _$StaffAssignmentItemModelImpl value,
    $Res Function(_$StaffAssignmentItemModelImpl) then,
  ) = __$$StaffAssignmentItemModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    @JsonKey(readValue: _readId) int id,
    @JsonKey(readValue: _readCompanyId) int? company,
    @JsonKey(readValue: _readCompanyName) String? companyName,
    int? department,
    String? departmentName,
    int? duty,
    String? dutyName,
    int? position,
    String? positionName,
    @JsonKey(readValue: _readDesc) String? assignedTasks,
    bool isPrimary,
  });
}

/// @nodoc
class __$$StaffAssignmentItemModelImplCopyWithImpl<$Res>
    extends
        _$StaffAssignmentItemModelCopyWithImpl<
          $Res,
          _$StaffAssignmentItemModelImpl
        >
    implements _$$StaffAssignmentItemModelImplCopyWith<$Res> {
  __$$StaffAssignmentItemModelImplCopyWithImpl(
    _$StaffAssignmentItemModelImpl _value,
    $Res Function(_$StaffAssignmentItemModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of StaffAssignmentItemModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? company = freezed,
    Object? companyName = freezed,
    Object? department = freezed,
    Object? departmentName = freezed,
    Object? duty = freezed,
    Object? dutyName = freezed,
    Object? position = freezed,
    Object? positionName = freezed,
    Object? assignedTasks = freezed,
    Object? isPrimary = null,
  }) {
    return _then(
      _$StaffAssignmentItemModelImpl(
        id: null == id
            ? _value.id
            : id // ignore: cast_nullable_to_non_nullable
                  as int,
        company: freezed == company
            ? _value.company
            : company // ignore: cast_nullable_to_non_nullable
                  as int?,
        companyName: freezed == companyName
            ? _value.companyName
            : companyName // ignore: cast_nullable_to_non_nullable
                  as String?,
        department: freezed == department
            ? _value.department
            : department // ignore: cast_nullable_to_non_nullable
                  as int?,
        departmentName: freezed == departmentName
            ? _value.departmentName
            : departmentName // ignore: cast_nullable_to_non_nullable
                  as String?,
        duty: freezed == duty
            ? _value.duty
            : duty // ignore: cast_nullable_to_non_nullable
                  as int?,
        dutyName: freezed == dutyName
            ? _value.dutyName
            : dutyName // ignore: cast_nullable_to_non_nullable
                  as String?,
        position: freezed == position
            ? _value.position
            : position // ignore: cast_nullable_to_non_nullable
                  as int?,
        positionName: freezed == positionName
            ? _value.positionName
            : positionName // ignore: cast_nullable_to_non_nullable
                  as String?,
        assignedTasks: freezed == assignedTasks
            ? _value.assignedTasks
            : assignedTasks // ignore: cast_nullable_to_non_nullable
                  as String?,
        isPrimary: null == isPrimary
            ? _value.isPrimary
            : isPrimary // ignore: cast_nullable_to_non_nullable
                  as bool,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$StaffAssignmentItemModelImpl implements _StaffAssignmentItemModel {
  const _$StaffAssignmentItemModelImpl({
    @JsonKey(readValue: _readId) required this.id,
    @JsonKey(readValue: _readCompanyId) this.company,
    @JsonKey(readValue: _readCompanyName) this.companyName,
    this.department,
    this.departmentName,
    this.duty,
    this.dutyName,
    this.position,
    this.positionName,
    @JsonKey(readValue: _readDesc) this.assignedTasks,
    this.isPrimary = false,
  });

  factory _$StaffAssignmentItemModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$StaffAssignmentItemModelImplFromJson(json);

  @override
  @JsonKey(readValue: _readId)
  final int id;
  @override
  @JsonKey(readValue: _readCompanyId)
  final int? company;
  @override
  @JsonKey(readValue: _readCompanyName)
  final String? companyName;
  @override
  final int? department;
  @override
  final String? departmentName;
  @override
  final int? duty;
  @override
  final String? dutyName;
  @override
  final int? position;
  @override
  final String? positionName;
  @override
  @JsonKey(readValue: _readDesc)
  final String? assignedTasks;
  @override
  @JsonKey()
  final bool isPrimary;

  @override
  String toString() {
    return 'StaffAssignmentItemModel(id: $id, company: $company, companyName: $companyName, department: $department, departmentName: $departmentName, duty: $duty, dutyName: $dutyName, position: $position, positionName: $positionName, assignedTasks: $assignedTasks, isPrimary: $isPrimary)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$StaffAssignmentItemModelImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.company, company) || other.company == company) &&
            (identical(other.companyName, companyName) ||
                other.companyName == companyName) &&
            (identical(other.department, department) ||
                other.department == department) &&
            (identical(other.departmentName, departmentName) ||
                other.departmentName == departmentName) &&
            (identical(other.duty, duty) || other.duty == duty) &&
            (identical(other.dutyName, dutyName) ||
                other.dutyName == dutyName) &&
            (identical(other.position, position) ||
                other.position == position) &&
            (identical(other.positionName, positionName) ||
                other.positionName == positionName) &&
            (identical(other.assignedTasks, assignedTasks) ||
                other.assignedTasks == assignedTasks) &&
            (identical(other.isPrimary, isPrimary) ||
                other.isPrimary == isPrimary));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
    runtimeType,
    id,
    company,
    companyName,
    department,
    departmentName,
    duty,
    dutyName,
    position,
    positionName,
    assignedTasks,
    isPrimary,
  );

  /// Create a copy of StaffAssignmentItemModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$StaffAssignmentItemModelImplCopyWith<_$StaffAssignmentItemModelImpl>
  get copyWith =>
      __$$StaffAssignmentItemModelImplCopyWithImpl<
        _$StaffAssignmentItemModelImpl
      >(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$StaffAssignmentItemModelImplToJson(this);
  }
}

abstract class _StaffAssignmentItemModel implements StaffAssignmentItemModel {
  const factory _StaffAssignmentItemModel({
    @JsonKey(readValue: _readId) required final int id,
    @JsonKey(readValue: _readCompanyId) final int? company,
    @JsonKey(readValue: _readCompanyName) final String? companyName,
    final int? department,
    final String? departmentName,
    final int? duty,
    final String? dutyName,
    final int? position,
    final String? positionName,
    @JsonKey(readValue: _readDesc) final String? assignedTasks,
    final bool isPrimary,
  }) = _$StaffAssignmentItemModelImpl;

  factory _StaffAssignmentItemModel.fromJson(Map<String, dynamic> json) =
      _$StaffAssignmentItemModelImpl.fromJson;

  @override
  @JsonKey(readValue: _readId)
  int get id;
  @override
  @JsonKey(readValue: _readCompanyId)
  int? get company;
  @override
  @JsonKey(readValue: _readCompanyName)
  String? get companyName;
  @override
  int? get department;
  @override
  String? get departmentName;
  @override
  int? get duty;
  @override
  String? get dutyName;
  @override
  int? get position;
  @override
  String? get positionName;
  @override
  @JsonKey(readValue: _readDesc)
  String? get assignedTasks;
  @override
  bool get isPrimary;

  /// Create a copy of StaffAssignmentItemModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$StaffAssignmentItemModelImplCopyWith<_$StaffAssignmentItemModelImpl>
  get copyWith => throw _privateConstructorUsedError;
}

ApprovalActionModel _$ApprovalActionModelFromJson(Map<String, dynamic> json) {
  return _ApprovalActionModel.fromJson(json);
}

/// @nodoc
mixin _$ApprovalActionModel {
  @JsonKey(readValue: _readId)
  int get id => throw _privateConstructorUsedError;
  SimpleUserModel get approver => throw _privateConstructorUsedError;
  bool get isDelegated => throw _privateConstructorUsedError;
  SimpleUserModel? get delegatedFrom => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get action => throw _privateConstructorUsedError; // approved, rejected, commented
  @JsonKey(readValue: _readStr)
  String get comment => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get contentHash => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get actedAt => throw _privateConstructorUsedError;

  /// Serializes this ApprovalActionModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ApprovalActionModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ApprovalActionModelCopyWith<ApprovalActionModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ApprovalActionModelCopyWith<$Res> {
  factory $ApprovalActionModelCopyWith(
    ApprovalActionModel value,
    $Res Function(ApprovalActionModel) then,
  ) = _$ApprovalActionModelCopyWithImpl<$Res, ApprovalActionModel>;
  @useResult
  $Res call({
    @JsonKey(readValue: _readId) int id,
    SimpleUserModel approver,
    bool isDelegated,
    SimpleUserModel? delegatedFrom,
    @JsonKey(readValue: _readStr) String action,
    @JsonKey(readValue: _readStr) String comment,
    @JsonKey(readValue: _readStr) String contentHash,
    @JsonKey(readValue: _readStr) String actedAt,
  });

  $SimpleUserModelCopyWith<$Res> get approver;
  $SimpleUserModelCopyWith<$Res>? get delegatedFrom;
}

/// @nodoc
class _$ApprovalActionModelCopyWithImpl<$Res, $Val extends ApprovalActionModel>
    implements $ApprovalActionModelCopyWith<$Res> {
  _$ApprovalActionModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ApprovalActionModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? approver = null,
    Object? isDelegated = null,
    Object? delegatedFrom = freezed,
    Object? action = null,
    Object? comment = null,
    Object? contentHash = null,
    Object? actedAt = null,
  }) {
    return _then(
      _value.copyWith(
            id: null == id
                ? _value.id
                : id // ignore: cast_nullable_to_non_nullable
                      as int,
            approver: null == approver
                ? _value.approver
                : approver // ignore: cast_nullable_to_non_nullable
                      as SimpleUserModel,
            isDelegated: null == isDelegated
                ? _value.isDelegated
                : isDelegated // ignore: cast_nullable_to_non_nullable
                      as bool,
            delegatedFrom: freezed == delegatedFrom
                ? _value.delegatedFrom
                : delegatedFrom // ignore: cast_nullable_to_non_nullable
                      as SimpleUserModel?,
            action: null == action
                ? _value.action
                : action // ignore: cast_nullable_to_non_nullable
                      as String,
            comment: null == comment
                ? _value.comment
                : comment // ignore: cast_nullable_to_non_nullable
                      as String,
            contentHash: null == contentHash
                ? _value.contentHash
                : contentHash // ignore: cast_nullable_to_non_nullable
                      as String,
            actedAt: null == actedAt
                ? _value.actedAt
                : actedAt // ignore: cast_nullable_to_non_nullable
                      as String,
          )
          as $Val,
    );
  }

  /// Create a copy of ApprovalActionModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SimpleUserModelCopyWith<$Res> get approver {
    return $SimpleUserModelCopyWith<$Res>(_value.approver, (value) {
      return _then(_value.copyWith(approver: value) as $Val);
    });
  }

  /// Create a copy of ApprovalActionModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SimpleUserModelCopyWith<$Res>? get delegatedFrom {
    if (_value.delegatedFrom == null) {
      return null;
    }

    return $SimpleUserModelCopyWith<$Res>(_value.delegatedFrom!, (value) {
      return _then(_value.copyWith(delegatedFrom: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$ApprovalActionModelImplCopyWith<$Res>
    implements $ApprovalActionModelCopyWith<$Res> {
  factory _$$ApprovalActionModelImplCopyWith(
    _$ApprovalActionModelImpl value,
    $Res Function(_$ApprovalActionModelImpl) then,
  ) = __$$ApprovalActionModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    @JsonKey(readValue: _readId) int id,
    SimpleUserModel approver,
    bool isDelegated,
    SimpleUserModel? delegatedFrom,
    @JsonKey(readValue: _readStr) String action,
    @JsonKey(readValue: _readStr) String comment,
    @JsonKey(readValue: _readStr) String contentHash,
    @JsonKey(readValue: _readStr) String actedAt,
  });

  @override
  $SimpleUserModelCopyWith<$Res> get approver;
  @override
  $SimpleUserModelCopyWith<$Res>? get delegatedFrom;
}

/// @nodoc
class __$$ApprovalActionModelImplCopyWithImpl<$Res>
    extends _$ApprovalActionModelCopyWithImpl<$Res, _$ApprovalActionModelImpl>
    implements _$$ApprovalActionModelImplCopyWith<$Res> {
  __$$ApprovalActionModelImplCopyWithImpl(
    _$ApprovalActionModelImpl _value,
    $Res Function(_$ApprovalActionModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of ApprovalActionModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? approver = null,
    Object? isDelegated = null,
    Object? delegatedFrom = freezed,
    Object? action = null,
    Object? comment = null,
    Object? contentHash = null,
    Object? actedAt = null,
  }) {
    return _then(
      _$ApprovalActionModelImpl(
        id: null == id
            ? _value.id
            : id // ignore: cast_nullable_to_non_nullable
                  as int,
        approver: null == approver
            ? _value.approver
            : approver // ignore: cast_nullable_to_non_nullable
                  as SimpleUserModel,
        isDelegated: null == isDelegated
            ? _value.isDelegated
            : isDelegated // ignore: cast_nullable_to_non_nullable
                  as bool,
        delegatedFrom: freezed == delegatedFrom
            ? _value.delegatedFrom
            : delegatedFrom // ignore: cast_nullable_to_non_nullable
                  as SimpleUserModel?,
        action: null == action
            ? _value.action
            : action // ignore: cast_nullable_to_non_nullable
                  as String,
        comment: null == comment
            ? _value.comment
            : comment // ignore: cast_nullable_to_non_nullable
                  as String,
        contentHash: null == contentHash
            ? _value.contentHash
            : contentHash // ignore: cast_nullable_to_non_nullable
                  as String,
        actedAt: null == actedAt
            ? _value.actedAt
            : actedAt // ignore: cast_nullable_to_non_nullable
                  as String,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$ApprovalActionModelImpl implements _ApprovalActionModel {
  const _$ApprovalActionModelImpl({
    @JsonKey(readValue: _readId) required this.id,
    required this.approver,
    this.isDelegated = false,
    this.delegatedFrom,
    @JsonKey(readValue: _readStr) this.action = 'approved',
    @JsonKey(readValue: _readStr) this.comment = '',
    @JsonKey(readValue: _readStr) this.contentHash = '',
    @JsonKey(readValue: _readStr) this.actedAt = '',
  });

  factory _$ApprovalActionModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$ApprovalActionModelImplFromJson(json);

  @override
  @JsonKey(readValue: _readId)
  final int id;
  @override
  final SimpleUserModel approver;
  @override
  @JsonKey()
  final bool isDelegated;
  @override
  final SimpleUserModel? delegatedFrom;
  @override
  @JsonKey(readValue: _readStr)
  final String action;
  // approved, rejected, commented
  @override
  @JsonKey(readValue: _readStr)
  final String comment;
  @override
  @JsonKey(readValue: _readStr)
  final String contentHash;
  @override
  @JsonKey(readValue: _readStr)
  final String actedAt;

  @override
  String toString() {
    return 'ApprovalActionModel(id: $id, approver: $approver, isDelegated: $isDelegated, delegatedFrom: $delegatedFrom, action: $action, comment: $comment, contentHash: $contentHash, actedAt: $actedAt)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ApprovalActionModelImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.approver, approver) ||
                other.approver == approver) &&
            (identical(other.isDelegated, isDelegated) ||
                other.isDelegated == isDelegated) &&
            (identical(other.delegatedFrom, delegatedFrom) ||
                other.delegatedFrom == delegatedFrom) &&
            (identical(other.action, action) || other.action == action) &&
            (identical(other.comment, comment) || other.comment == comment) &&
            (identical(other.contentHash, contentHash) ||
                other.contentHash == contentHash) &&
            (identical(other.actedAt, actedAt) || other.actedAt == actedAt));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
    runtimeType,
    id,
    approver,
    isDelegated,
    delegatedFrom,
    action,
    comment,
    contentHash,
    actedAt,
  );

  /// Create a copy of ApprovalActionModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ApprovalActionModelImplCopyWith<_$ApprovalActionModelImpl> get copyWith =>
      __$$ApprovalActionModelImplCopyWithImpl<_$ApprovalActionModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$ApprovalActionModelImplToJson(this);
  }
}

abstract class _ApprovalActionModel implements ApprovalActionModel {
  const factory _ApprovalActionModel({
    @JsonKey(readValue: _readId) required final int id,
    required final SimpleUserModel approver,
    final bool isDelegated,
    final SimpleUserModel? delegatedFrom,
    @JsonKey(readValue: _readStr) final String action,
    @JsonKey(readValue: _readStr) final String comment,
    @JsonKey(readValue: _readStr) final String contentHash,
    @JsonKey(readValue: _readStr) final String actedAt,
  }) = _$ApprovalActionModelImpl;

  factory _ApprovalActionModel.fromJson(Map<String, dynamic> json) =
      _$ApprovalActionModelImpl.fromJson;

  @override
  @JsonKey(readValue: _readId)
  int get id;
  @override
  SimpleUserModel get approver;
  @override
  bool get isDelegated;
  @override
  SimpleUserModel? get delegatedFrom;
  @override
  @JsonKey(readValue: _readStr)
  String get action; // approved, rejected, commented
  @override
  @JsonKey(readValue: _readStr)
  String get comment;
  @override
  @JsonKey(readValue: _readStr)
  String get contentHash;
  @override
  @JsonKey(readValue: _readStr)
  String get actedAt;

  /// Create a copy of ApprovalActionModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ApprovalActionModelImplCopyWith<_$ApprovalActionModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ApprovalAttachmentModel _$ApprovalAttachmentModelFromJson(
  Map<String, dynamic> json,
) {
  return _ApprovalAttachmentModel.fromJson(json);
}

/// @nodoc
mixin _$ApprovalAttachmentModel {
  @JsonKey(readValue: _readId)
  int get id => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readId)
  int get document => throw _privateConstructorUsedError;
  String? get file => throw _privateConstructorUsedError;
  String? get fileUrl => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get fileName => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get fileType => throw _privateConstructorUsedError;
  int? get fileSize => throw _privateConstructorUsedError;
  String? get creatorName => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get createdAt => throw _privateConstructorUsedError;

  /// Serializes this ApprovalAttachmentModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ApprovalAttachmentModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ApprovalAttachmentModelCopyWith<ApprovalAttachmentModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ApprovalAttachmentModelCopyWith<$Res> {
  factory $ApprovalAttachmentModelCopyWith(
    ApprovalAttachmentModel value,
    $Res Function(ApprovalAttachmentModel) then,
  ) = _$ApprovalAttachmentModelCopyWithImpl<$Res, ApprovalAttachmentModel>;
  @useResult
  $Res call({
    @JsonKey(readValue: _readId) int id,
    @JsonKey(readValue: _readId) int document,
    String? file,
    String? fileUrl,
    @JsonKey(readValue: _readStr) String fileName,
    @JsonKey(readValue: _readStr) String fileType,
    int? fileSize,
    String? creatorName,
    @JsonKey(readValue: _readStr) String createdAt,
  });
}

/// @nodoc
class _$ApprovalAttachmentModelCopyWithImpl<
  $Res,
  $Val extends ApprovalAttachmentModel
>
    implements $ApprovalAttachmentModelCopyWith<$Res> {
  _$ApprovalAttachmentModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ApprovalAttachmentModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? document = null,
    Object? file = freezed,
    Object? fileUrl = freezed,
    Object? fileName = null,
    Object? fileType = null,
    Object? fileSize = freezed,
    Object? creatorName = freezed,
    Object? createdAt = null,
  }) {
    return _then(
      _value.copyWith(
            id: null == id
                ? _value.id
                : id // ignore: cast_nullable_to_non_nullable
                      as int,
            document: null == document
                ? _value.document
                : document // ignore: cast_nullable_to_non_nullable
                      as int,
            file: freezed == file
                ? _value.file
                : file // ignore: cast_nullable_to_non_nullable
                      as String?,
            fileUrl: freezed == fileUrl
                ? _value.fileUrl
                : fileUrl // ignore: cast_nullable_to_non_nullable
                      as String?,
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
            creatorName: freezed == creatorName
                ? _value.creatorName
                : creatorName // ignore: cast_nullable_to_non_nullable
                      as String?,
            createdAt: null == createdAt
                ? _value.createdAt
                : createdAt // ignore: cast_nullable_to_non_nullable
                      as String,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$ApprovalAttachmentModelImplCopyWith<$Res>
    implements $ApprovalAttachmentModelCopyWith<$Res> {
  factory _$$ApprovalAttachmentModelImplCopyWith(
    _$ApprovalAttachmentModelImpl value,
    $Res Function(_$ApprovalAttachmentModelImpl) then,
  ) = __$$ApprovalAttachmentModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    @JsonKey(readValue: _readId) int id,
    @JsonKey(readValue: _readId) int document,
    String? file,
    String? fileUrl,
    @JsonKey(readValue: _readStr) String fileName,
    @JsonKey(readValue: _readStr) String fileType,
    int? fileSize,
    String? creatorName,
    @JsonKey(readValue: _readStr) String createdAt,
  });
}

/// @nodoc
class __$$ApprovalAttachmentModelImplCopyWithImpl<$Res>
    extends
        _$ApprovalAttachmentModelCopyWithImpl<
          $Res,
          _$ApprovalAttachmentModelImpl
        >
    implements _$$ApprovalAttachmentModelImplCopyWith<$Res> {
  __$$ApprovalAttachmentModelImplCopyWithImpl(
    _$ApprovalAttachmentModelImpl _value,
    $Res Function(_$ApprovalAttachmentModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of ApprovalAttachmentModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? document = null,
    Object? file = freezed,
    Object? fileUrl = freezed,
    Object? fileName = null,
    Object? fileType = null,
    Object? fileSize = freezed,
    Object? creatorName = freezed,
    Object? createdAt = null,
  }) {
    return _then(
      _$ApprovalAttachmentModelImpl(
        id: null == id
            ? _value.id
            : id // ignore: cast_nullable_to_non_nullable
                  as int,
        document: null == document
            ? _value.document
            : document // ignore: cast_nullable_to_non_nullable
                  as int,
        file: freezed == file
            ? _value.file
            : file // ignore: cast_nullable_to_non_nullable
                  as String?,
        fileUrl: freezed == fileUrl
            ? _value.fileUrl
            : fileUrl // ignore: cast_nullable_to_non_nullable
                  as String?,
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
        creatorName: freezed == creatorName
            ? _value.creatorName
            : creatorName // ignore: cast_nullable_to_non_nullable
                  as String?,
        createdAt: null == createdAt
            ? _value.createdAt
            : createdAt // ignore: cast_nullable_to_non_nullable
                  as String,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$ApprovalAttachmentModelImpl implements _ApprovalAttachmentModel {
  const _$ApprovalAttachmentModelImpl({
    @JsonKey(readValue: _readId) required this.id,
    @JsonKey(readValue: _readId) required this.document,
    this.file,
    this.fileUrl,
    @JsonKey(readValue: _readStr) this.fileName = '',
    @JsonKey(readValue: _readStr) this.fileType = '',
    this.fileSize,
    this.creatorName,
    @JsonKey(readValue: _readStr) this.createdAt = '',
  });

  factory _$ApprovalAttachmentModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$ApprovalAttachmentModelImplFromJson(json);

  @override
  @JsonKey(readValue: _readId)
  final int id;
  @override
  @JsonKey(readValue: _readId)
  final int document;
  @override
  final String? file;
  @override
  final String? fileUrl;
  @override
  @JsonKey(readValue: _readStr)
  final String fileName;
  @override
  @JsonKey(readValue: _readStr)
  final String fileType;
  @override
  final int? fileSize;
  @override
  final String? creatorName;
  @override
  @JsonKey(readValue: _readStr)
  final String createdAt;

  @override
  String toString() {
    return 'ApprovalAttachmentModel(id: $id, document: $document, file: $file, fileUrl: $fileUrl, fileName: $fileName, fileType: $fileType, fileSize: $fileSize, creatorName: $creatorName, createdAt: $createdAt)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ApprovalAttachmentModelImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.document, document) ||
                other.document == document) &&
            (identical(other.file, file) || other.file == file) &&
            (identical(other.fileUrl, fileUrl) || other.fileUrl == fileUrl) &&
            (identical(other.fileName, fileName) ||
                other.fileName == fileName) &&
            (identical(other.fileType, fileType) ||
                other.fileType == fileType) &&
            (identical(other.fileSize, fileSize) ||
                other.fileSize == fileSize) &&
            (identical(other.creatorName, creatorName) ||
                other.creatorName == creatorName) &&
            (identical(other.createdAt, createdAt) ||
                other.createdAt == createdAt));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
    runtimeType,
    id,
    document,
    file,
    fileUrl,
    fileName,
    fileType,
    fileSize,
    creatorName,
    createdAt,
  );

  /// Create a copy of ApprovalAttachmentModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ApprovalAttachmentModelImplCopyWith<_$ApprovalAttachmentModelImpl>
  get copyWith =>
      __$$ApprovalAttachmentModelImplCopyWithImpl<
        _$ApprovalAttachmentModelImpl
      >(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ApprovalAttachmentModelImplToJson(this);
  }
}

abstract class _ApprovalAttachmentModel implements ApprovalAttachmentModel {
  const factory _ApprovalAttachmentModel({
    @JsonKey(readValue: _readId) required final int id,
    @JsonKey(readValue: _readId) required final int document,
    final String? file,
    final String? fileUrl,
    @JsonKey(readValue: _readStr) final String fileName,
    @JsonKey(readValue: _readStr) final String fileType,
    final int? fileSize,
    final String? creatorName,
    @JsonKey(readValue: _readStr) final String createdAt,
  }) = _$ApprovalAttachmentModelImpl;

  factory _ApprovalAttachmentModel.fromJson(Map<String, dynamic> json) =
      _$ApprovalAttachmentModelImpl.fromJson;

  @override
  @JsonKey(readValue: _readId)
  int get id;
  @override
  @JsonKey(readValue: _readId)
  int get document;
  @override
  String? get file;
  @override
  String? get fileUrl;
  @override
  @JsonKey(readValue: _readStr)
  String get fileName;
  @override
  @JsonKey(readValue: _readStr)
  String get fileType;
  @override
  int? get fileSize;
  @override
  String? get creatorName;
  @override
  @JsonKey(readValue: _readStr)
  String get createdAt;

  /// Create a copy of ApprovalAttachmentModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ApprovalAttachmentModelImplCopyWith<_$ApprovalAttachmentModelImpl>
  get copyWith => throw _privateConstructorUsedError;
}

ApprovalStepModel _$ApprovalStepModelFromJson(Map<String, dynamic> json) {
  return _ApprovalStepModel.fromJson(json);
}

/// @nodoc
mixin _$ApprovalStepModel {
  @JsonKey(readValue: _readId)
  int get id => throw _privateConstructorUsedError;
  int get stepOrder => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get roleLabel => throw _privateConstructorUsedError;
  List<SimpleUserModel> get approvers => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get condition => throw _privateConstructorUsedError; // AND, OR
  @JsonKey(readValue: _readStr)
  String get status => throw _privateConstructorUsedError; // pending, approved, rejected, skipped
  List<ApprovalActionModel> get actions => throw _privateConstructorUsedError;

  /// Serializes this ApprovalStepModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ApprovalStepModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ApprovalStepModelCopyWith<ApprovalStepModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ApprovalStepModelCopyWith<$Res> {
  factory $ApprovalStepModelCopyWith(
    ApprovalStepModel value,
    $Res Function(ApprovalStepModel) then,
  ) = _$ApprovalStepModelCopyWithImpl<$Res, ApprovalStepModel>;
  @useResult
  $Res call({
    @JsonKey(readValue: _readId) int id,
    int stepOrder,
    @JsonKey(readValue: _readStr) String roleLabel,
    List<SimpleUserModel> approvers,
    @JsonKey(readValue: _readStr) String condition,
    @JsonKey(readValue: _readStr) String status,
    List<ApprovalActionModel> actions,
  });
}

/// @nodoc
class _$ApprovalStepModelCopyWithImpl<$Res, $Val extends ApprovalStepModel>
    implements $ApprovalStepModelCopyWith<$Res> {
  _$ApprovalStepModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ApprovalStepModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? stepOrder = null,
    Object? roleLabel = null,
    Object? approvers = null,
    Object? condition = null,
    Object? status = null,
    Object? actions = null,
  }) {
    return _then(
      _value.copyWith(
            id: null == id
                ? _value.id
                : id // ignore: cast_nullable_to_non_nullable
                      as int,
            stepOrder: null == stepOrder
                ? _value.stepOrder
                : stepOrder // ignore: cast_nullable_to_non_nullable
                      as int,
            roleLabel: null == roleLabel
                ? _value.roleLabel
                : roleLabel // ignore: cast_nullable_to_non_nullable
                      as String,
            approvers: null == approvers
                ? _value.approvers
                : approvers // ignore: cast_nullable_to_non_nullable
                      as List<SimpleUserModel>,
            condition: null == condition
                ? _value.condition
                : condition // ignore: cast_nullable_to_non_nullable
                      as String,
            status: null == status
                ? _value.status
                : status // ignore: cast_nullable_to_non_nullable
                      as String,
            actions: null == actions
                ? _value.actions
                : actions // ignore: cast_nullable_to_non_nullable
                      as List<ApprovalActionModel>,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$ApprovalStepModelImplCopyWith<$Res>
    implements $ApprovalStepModelCopyWith<$Res> {
  factory _$$ApprovalStepModelImplCopyWith(
    _$ApprovalStepModelImpl value,
    $Res Function(_$ApprovalStepModelImpl) then,
  ) = __$$ApprovalStepModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    @JsonKey(readValue: _readId) int id,
    int stepOrder,
    @JsonKey(readValue: _readStr) String roleLabel,
    List<SimpleUserModel> approvers,
    @JsonKey(readValue: _readStr) String condition,
    @JsonKey(readValue: _readStr) String status,
    List<ApprovalActionModel> actions,
  });
}

/// @nodoc
class __$$ApprovalStepModelImplCopyWithImpl<$Res>
    extends _$ApprovalStepModelCopyWithImpl<$Res, _$ApprovalStepModelImpl>
    implements _$$ApprovalStepModelImplCopyWith<$Res> {
  __$$ApprovalStepModelImplCopyWithImpl(
    _$ApprovalStepModelImpl _value,
    $Res Function(_$ApprovalStepModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of ApprovalStepModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? stepOrder = null,
    Object? roleLabel = null,
    Object? approvers = null,
    Object? condition = null,
    Object? status = null,
    Object? actions = null,
  }) {
    return _then(
      _$ApprovalStepModelImpl(
        id: null == id
            ? _value.id
            : id // ignore: cast_nullable_to_non_nullable
                  as int,
        stepOrder: null == stepOrder
            ? _value.stepOrder
            : stepOrder // ignore: cast_nullable_to_non_nullable
                  as int,
        roleLabel: null == roleLabel
            ? _value.roleLabel
            : roleLabel // ignore: cast_nullable_to_non_nullable
                  as String,
        approvers: null == approvers
            ? _value._approvers
            : approvers // ignore: cast_nullable_to_non_nullable
                  as List<SimpleUserModel>,
        condition: null == condition
            ? _value.condition
            : condition // ignore: cast_nullable_to_non_nullable
                  as String,
        status: null == status
            ? _value.status
            : status // ignore: cast_nullable_to_non_nullable
                  as String,
        actions: null == actions
            ? _value._actions
            : actions // ignore: cast_nullable_to_non_nullable
                  as List<ApprovalActionModel>,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$ApprovalStepModelImpl implements _ApprovalStepModel {
  const _$ApprovalStepModelImpl({
    @JsonKey(readValue: _readId) required this.id,
    required this.stepOrder,
    @JsonKey(readValue: _readStr) this.roleLabel = '',
    final List<SimpleUserModel> approvers = const [],
    @JsonKey(readValue: _readStr) this.condition = 'AND',
    @JsonKey(readValue: _readStr) this.status = 'pending',
    final List<ApprovalActionModel> actions = const [],
  }) : _approvers = approvers,
       _actions = actions;

  factory _$ApprovalStepModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$ApprovalStepModelImplFromJson(json);

  @override
  @JsonKey(readValue: _readId)
  final int id;
  @override
  final int stepOrder;
  @override
  @JsonKey(readValue: _readStr)
  final String roleLabel;
  final List<SimpleUserModel> _approvers;
  @override
  @JsonKey()
  List<SimpleUserModel> get approvers {
    if (_approvers is EqualUnmodifiableListView) return _approvers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_approvers);
  }

  @override
  @JsonKey(readValue: _readStr)
  final String condition;
  // AND, OR
  @override
  @JsonKey(readValue: _readStr)
  final String status;
  // pending, approved, rejected, skipped
  final List<ApprovalActionModel> _actions;
  // pending, approved, rejected, skipped
  @override
  @JsonKey()
  List<ApprovalActionModel> get actions {
    if (_actions is EqualUnmodifiableListView) return _actions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_actions);
  }

  @override
  String toString() {
    return 'ApprovalStepModel(id: $id, stepOrder: $stepOrder, roleLabel: $roleLabel, approvers: $approvers, condition: $condition, status: $status, actions: $actions)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ApprovalStepModelImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.stepOrder, stepOrder) ||
                other.stepOrder == stepOrder) &&
            (identical(other.roleLabel, roleLabel) ||
                other.roleLabel == roleLabel) &&
            const DeepCollectionEquality().equals(
              other._approvers,
              _approvers,
            ) &&
            (identical(other.condition, condition) ||
                other.condition == condition) &&
            (identical(other.status, status) || other.status == status) &&
            const DeepCollectionEquality().equals(other._actions, _actions));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
    runtimeType,
    id,
    stepOrder,
    roleLabel,
    const DeepCollectionEquality().hash(_approvers),
    condition,
    status,
    const DeepCollectionEquality().hash(_actions),
  );

  /// Create a copy of ApprovalStepModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ApprovalStepModelImplCopyWith<_$ApprovalStepModelImpl> get copyWith =>
      __$$ApprovalStepModelImplCopyWithImpl<_$ApprovalStepModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$ApprovalStepModelImplToJson(this);
  }
}

abstract class _ApprovalStepModel implements ApprovalStepModel {
  const factory _ApprovalStepModel({
    @JsonKey(readValue: _readId) required final int id,
    required final int stepOrder,
    @JsonKey(readValue: _readStr) final String roleLabel,
    final List<SimpleUserModel> approvers,
    @JsonKey(readValue: _readStr) final String condition,
    @JsonKey(readValue: _readStr) final String status,
    final List<ApprovalActionModel> actions,
  }) = _$ApprovalStepModelImpl;

  factory _ApprovalStepModel.fromJson(Map<String, dynamic> json) =
      _$ApprovalStepModelImpl.fromJson;

  @override
  @JsonKey(readValue: _readId)
  int get id;
  @override
  int get stepOrder;
  @override
  @JsonKey(readValue: _readStr)
  String get roleLabel;
  @override
  List<SimpleUserModel> get approvers;
  @override
  @JsonKey(readValue: _readStr)
  String get condition; // AND, OR
  @override
  @JsonKey(readValue: _readStr)
  String get status; // pending, approved, rejected, skipped
  @override
  List<ApprovalActionModel> get actions;

  /// Create a copy of ApprovalStepModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ApprovalStepModelImplCopyWith<_$ApprovalStepModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

RoutePreviewStepModel _$RoutePreviewStepModelFromJson(
  Map<String, dynamic> json,
) {
  return _RoutePreviewStepModel.fromJson(json);
}

/// @nodoc
mixin _$RoutePreviewStepModel {
  int get stepOrder => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get roleLabel => throw _privateConstructorUsedError;
  List<SimpleUserModel> get approvers => throw _privateConstructorUsedError;
  List<int> get approverIds => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get condition => throw _privateConstructorUsedError;

  /// Serializes this RoutePreviewStepModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of RoutePreviewStepModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $RoutePreviewStepModelCopyWith<RoutePreviewStepModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $RoutePreviewStepModelCopyWith<$Res> {
  factory $RoutePreviewStepModelCopyWith(
    RoutePreviewStepModel value,
    $Res Function(RoutePreviewStepModel) then,
  ) = _$RoutePreviewStepModelCopyWithImpl<$Res, RoutePreviewStepModel>;
  @useResult
  $Res call({
    int stepOrder,
    @JsonKey(readValue: _readStr) String roleLabel,
    List<SimpleUserModel> approvers,
    List<int> approverIds,
    @JsonKey(readValue: _readStr) String condition,
  });
}

/// @nodoc
class _$RoutePreviewStepModelCopyWithImpl<
  $Res,
  $Val extends RoutePreviewStepModel
>
    implements $RoutePreviewStepModelCopyWith<$Res> {
  _$RoutePreviewStepModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of RoutePreviewStepModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? stepOrder = null,
    Object? roleLabel = null,
    Object? approvers = null,
    Object? approverIds = null,
    Object? condition = null,
  }) {
    return _then(
      _value.copyWith(
            stepOrder: null == stepOrder
                ? _value.stepOrder
                : stepOrder // ignore: cast_nullable_to_non_nullable
                      as int,
            roleLabel: null == roleLabel
                ? _value.roleLabel
                : roleLabel // ignore: cast_nullable_to_non_nullable
                      as String,
            approvers: null == approvers
                ? _value.approvers
                : approvers // ignore: cast_nullable_to_non_nullable
                      as List<SimpleUserModel>,
            approverIds: null == approverIds
                ? _value.approverIds
                : approverIds // ignore: cast_nullable_to_non_nullable
                      as List<int>,
            condition: null == condition
                ? _value.condition
                : condition // ignore: cast_nullable_to_non_nullable
                      as String,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$RoutePreviewStepModelImplCopyWith<$Res>
    implements $RoutePreviewStepModelCopyWith<$Res> {
  factory _$$RoutePreviewStepModelImplCopyWith(
    _$RoutePreviewStepModelImpl value,
    $Res Function(_$RoutePreviewStepModelImpl) then,
  ) = __$$RoutePreviewStepModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int stepOrder,
    @JsonKey(readValue: _readStr) String roleLabel,
    List<SimpleUserModel> approvers,
    List<int> approverIds,
    @JsonKey(readValue: _readStr) String condition,
  });
}

/// @nodoc
class __$$RoutePreviewStepModelImplCopyWithImpl<$Res>
    extends
        _$RoutePreviewStepModelCopyWithImpl<$Res, _$RoutePreviewStepModelImpl>
    implements _$$RoutePreviewStepModelImplCopyWith<$Res> {
  __$$RoutePreviewStepModelImplCopyWithImpl(
    _$RoutePreviewStepModelImpl _value,
    $Res Function(_$RoutePreviewStepModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of RoutePreviewStepModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? stepOrder = null,
    Object? roleLabel = null,
    Object? approvers = null,
    Object? approverIds = null,
    Object? condition = null,
  }) {
    return _then(
      _$RoutePreviewStepModelImpl(
        stepOrder: null == stepOrder
            ? _value.stepOrder
            : stepOrder // ignore: cast_nullable_to_non_nullable
                  as int,
        roleLabel: null == roleLabel
            ? _value.roleLabel
            : roleLabel // ignore: cast_nullable_to_non_nullable
                  as String,
        approvers: null == approvers
            ? _value._approvers
            : approvers // ignore: cast_nullable_to_non_nullable
                  as List<SimpleUserModel>,
        approverIds: null == approverIds
            ? _value._approverIds
            : approverIds // ignore: cast_nullable_to_non_nullable
                  as List<int>,
        condition: null == condition
            ? _value.condition
            : condition // ignore: cast_nullable_to_non_nullable
                  as String,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$RoutePreviewStepModelImpl implements _RoutePreviewStepModel {
  const _$RoutePreviewStepModelImpl({
    required this.stepOrder,
    @JsonKey(readValue: _readStr) this.roleLabel = '',
    final List<SimpleUserModel> approvers = const [],
    final List<int> approverIds = const [],
    @JsonKey(readValue: _readStr) this.condition = 'AND',
  }) : _approvers = approvers,
       _approverIds = approverIds;

  factory _$RoutePreviewStepModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$RoutePreviewStepModelImplFromJson(json);

  @override
  final int stepOrder;
  @override
  @JsonKey(readValue: _readStr)
  final String roleLabel;
  final List<SimpleUserModel> _approvers;
  @override
  @JsonKey()
  List<SimpleUserModel> get approvers {
    if (_approvers is EqualUnmodifiableListView) return _approvers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_approvers);
  }

  final List<int> _approverIds;
  @override
  @JsonKey()
  List<int> get approverIds {
    if (_approverIds is EqualUnmodifiableListView) return _approverIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_approverIds);
  }

  @override
  @JsonKey(readValue: _readStr)
  final String condition;

  @override
  String toString() {
    return 'RoutePreviewStepModel(stepOrder: $stepOrder, roleLabel: $roleLabel, approvers: $approvers, approverIds: $approverIds, condition: $condition)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RoutePreviewStepModelImpl &&
            (identical(other.stepOrder, stepOrder) ||
                other.stepOrder == stepOrder) &&
            (identical(other.roleLabel, roleLabel) ||
                other.roleLabel == roleLabel) &&
            const DeepCollectionEquality().equals(
              other._approvers,
              _approvers,
            ) &&
            const DeepCollectionEquality().equals(
              other._approverIds,
              _approverIds,
            ) &&
            (identical(other.condition, condition) ||
                other.condition == condition));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
    runtimeType,
    stepOrder,
    roleLabel,
    const DeepCollectionEquality().hash(_approvers),
    const DeepCollectionEquality().hash(_approverIds),
    condition,
  );

  /// Create a copy of RoutePreviewStepModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$RoutePreviewStepModelImplCopyWith<_$RoutePreviewStepModelImpl>
  get copyWith =>
      __$$RoutePreviewStepModelImplCopyWithImpl<_$RoutePreviewStepModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$RoutePreviewStepModelImplToJson(this);
  }
}

abstract class _RoutePreviewStepModel implements RoutePreviewStepModel {
  const factory _RoutePreviewStepModel({
    required final int stepOrder,
    @JsonKey(readValue: _readStr) final String roleLabel,
    final List<SimpleUserModel> approvers,
    final List<int> approverIds,
    @JsonKey(readValue: _readStr) final String condition,
  }) = _$RoutePreviewStepModelImpl;

  factory _RoutePreviewStepModel.fromJson(Map<String, dynamic> json) =
      _$RoutePreviewStepModelImpl.fromJson;

  @override
  int get stepOrder;
  @override
  @JsonKey(readValue: _readStr)
  String get roleLabel;
  @override
  List<SimpleUserModel> get approvers;
  @override
  List<int> get approverIds;
  @override
  @JsonKey(readValue: _readStr)
  String get condition;

  /// Create a copy of RoutePreviewStepModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$RoutePreviewStepModelImplCopyWith<_$RoutePreviewStepModelImpl>
  get copyWith => throw _privateConstructorUsedError;
}

ApprovalDocumentModel _$ApprovalDocumentModelFromJson(
  Map<String, dynamic> json,
) {
  return _ApprovalDocumentModel.fromJson(json);
}

/// @nodoc
mixin _$ApprovalDocumentModel {
  @JsonKey(readValue: _readId)
  int get id => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get docNumber => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get title => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readDocTypeId)
  int get docType => throw _privateConstructorUsedError;
  String? get docTypeName => throw _privateConstructorUsedError;
  String? get categoryName => throw _privateConstructorUsedError;
  DocumentTypeModel? get docTypeDetail => throw _privateConstructorUsedError;
  SimpleUserModel get drafter => throw _privateConstructorUsedError;
  String? get drafterName => throw _privateConstructorUsedError;
  int? get drafterAssignment => throw _privateConstructorUsedError;
  String? get departmentName => throw _privateConstructorUsedError;
  String? get drafterAssignmentDesc => throw _privateConstructorUsedError;
  Map<String, dynamic> get content => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get status => throw _privateConstructorUsedError; // draft, pending, approved, rejected, cancelled
  String? get statusDesc => throw _privateConstructorUsedError;
  int get currentStep => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get contentHash => throw _privateConstructorUsedError;
  String? get pdfUrl => throw _privateConstructorUsedError;
  int get attachmentCount => throw _privateConstructorUsedError;
  int get observerCount => throw _privateConstructorUsedError;
  List<ApprovalAttachmentModel>? get attachments =>
      throw _privateConstructorUsedError;
  List<SimpleUserModel>? get observers => throw _privateConstructorUsedError;
  List<ApprovalStepModel>? get steps => throw _privateConstructorUsedError;
  @JsonKey(readValue: _readStr)
  String get createdAt => throw _privateConstructorUsedError;
  String? get submittedAt => throw _privateConstructorUsedError;
  String? get completedAt => throw _privateConstructorUsedError;

  /// Serializes this ApprovalDocumentModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ApprovalDocumentModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ApprovalDocumentModelCopyWith<ApprovalDocumentModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ApprovalDocumentModelCopyWith<$Res> {
  factory $ApprovalDocumentModelCopyWith(
    ApprovalDocumentModel value,
    $Res Function(ApprovalDocumentModel) then,
  ) = _$ApprovalDocumentModelCopyWithImpl<$Res, ApprovalDocumentModel>;
  @useResult
  $Res call({
    @JsonKey(readValue: _readId) int id,
    @JsonKey(readValue: _readStr) String docNumber,
    @JsonKey(readValue: _readStr) String title,
    @JsonKey(readValue: _readDocTypeId) int docType,
    String? docTypeName,
    String? categoryName,
    DocumentTypeModel? docTypeDetail,
    SimpleUserModel drafter,
    String? drafterName,
    int? drafterAssignment,
    String? departmentName,
    String? drafterAssignmentDesc,
    Map<String, dynamic> content,
    @JsonKey(readValue: _readStr) String status,
    String? statusDesc,
    int currentStep,
    @JsonKey(readValue: _readStr) String contentHash,
    String? pdfUrl,
    int attachmentCount,
    int observerCount,
    List<ApprovalAttachmentModel>? attachments,
    List<SimpleUserModel>? observers,
    List<ApprovalStepModel>? steps,
    @JsonKey(readValue: _readStr) String createdAt,
    String? submittedAt,
    String? completedAt,
  });

  $DocumentTypeModelCopyWith<$Res>? get docTypeDetail;
  $SimpleUserModelCopyWith<$Res> get drafter;
}

/// @nodoc
class _$ApprovalDocumentModelCopyWithImpl<
  $Res,
  $Val extends ApprovalDocumentModel
>
    implements $ApprovalDocumentModelCopyWith<$Res> {
  _$ApprovalDocumentModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ApprovalDocumentModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? docNumber = null,
    Object? title = null,
    Object? docType = null,
    Object? docTypeName = freezed,
    Object? categoryName = freezed,
    Object? docTypeDetail = freezed,
    Object? drafter = null,
    Object? drafterName = freezed,
    Object? drafterAssignment = freezed,
    Object? departmentName = freezed,
    Object? drafterAssignmentDesc = freezed,
    Object? content = null,
    Object? status = null,
    Object? statusDesc = freezed,
    Object? currentStep = null,
    Object? contentHash = null,
    Object? pdfUrl = freezed,
    Object? attachmentCount = null,
    Object? observerCount = null,
    Object? attachments = freezed,
    Object? observers = freezed,
    Object? steps = freezed,
    Object? createdAt = null,
    Object? submittedAt = freezed,
    Object? completedAt = freezed,
  }) {
    return _then(
      _value.copyWith(
            id: null == id
                ? _value.id
                : id // ignore: cast_nullable_to_non_nullable
                      as int,
            docNumber: null == docNumber
                ? _value.docNumber
                : docNumber // ignore: cast_nullable_to_non_nullable
                      as String,
            title: null == title
                ? _value.title
                : title // ignore: cast_nullable_to_non_nullable
                      as String,
            docType: null == docType
                ? _value.docType
                : docType // ignore: cast_nullable_to_non_nullable
                      as int,
            docTypeName: freezed == docTypeName
                ? _value.docTypeName
                : docTypeName // ignore: cast_nullable_to_non_nullable
                      as String?,
            categoryName: freezed == categoryName
                ? _value.categoryName
                : categoryName // ignore: cast_nullable_to_non_nullable
                      as String?,
            docTypeDetail: freezed == docTypeDetail
                ? _value.docTypeDetail
                : docTypeDetail // ignore: cast_nullable_to_non_nullable
                      as DocumentTypeModel?,
            drafter: null == drafter
                ? _value.drafter
                : drafter // ignore: cast_nullable_to_non_nullable
                      as SimpleUserModel,
            drafterName: freezed == drafterName
                ? _value.drafterName
                : drafterName // ignore: cast_nullable_to_non_nullable
                      as String?,
            drafterAssignment: freezed == drafterAssignment
                ? _value.drafterAssignment
                : drafterAssignment // ignore: cast_nullable_to_non_nullable
                      as int?,
            departmentName: freezed == departmentName
                ? _value.departmentName
                : departmentName // ignore: cast_nullable_to_non_nullable
                      as String?,
            drafterAssignmentDesc: freezed == drafterAssignmentDesc
                ? _value.drafterAssignmentDesc
                : drafterAssignmentDesc // ignore: cast_nullable_to_non_nullable
                      as String?,
            content: null == content
                ? _value.content
                : content // ignore: cast_nullable_to_non_nullable
                      as Map<String, dynamic>,
            status: null == status
                ? _value.status
                : status // ignore: cast_nullable_to_non_nullable
                      as String,
            statusDesc: freezed == statusDesc
                ? _value.statusDesc
                : statusDesc // ignore: cast_nullable_to_non_nullable
                      as String?,
            currentStep: null == currentStep
                ? _value.currentStep
                : currentStep // ignore: cast_nullable_to_non_nullable
                      as int,
            contentHash: null == contentHash
                ? _value.contentHash
                : contentHash // ignore: cast_nullable_to_non_nullable
                      as String,
            pdfUrl: freezed == pdfUrl
                ? _value.pdfUrl
                : pdfUrl // ignore: cast_nullable_to_non_nullable
                      as String?,
            attachmentCount: null == attachmentCount
                ? _value.attachmentCount
                : attachmentCount // ignore: cast_nullable_to_non_nullable
                      as int,
            observerCount: null == observerCount
                ? _value.observerCount
                : observerCount // ignore: cast_nullable_to_non_nullable
                      as int,
            attachments: freezed == attachments
                ? _value.attachments
                : attachments // ignore: cast_nullable_to_non_nullable
                      as List<ApprovalAttachmentModel>?,
            observers: freezed == observers
                ? _value.observers
                : observers // ignore: cast_nullable_to_non_nullable
                      as List<SimpleUserModel>?,
            steps: freezed == steps
                ? _value.steps
                : steps // ignore: cast_nullable_to_non_nullable
                      as List<ApprovalStepModel>?,
            createdAt: null == createdAt
                ? _value.createdAt
                : createdAt // ignore: cast_nullable_to_non_nullable
                      as String,
            submittedAt: freezed == submittedAt
                ? _value.submittedAt
                : submittedAt // ignore: cast_nullable_to_non_nullable
                      as String?,
            completedAt: freezed == completedAt
                ? _value.completedAt
                : completedAt // ignore: cast_nullable_to_non_nullable
                      as String?,
          )
          as $Val,
    );
  }

  /// Create a copy of ApprovalDocumentModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $DocumentTypeModelCopyWith<$Res>? get docTypeDetail {
    if (_value.docTypeDetail == null) {
      return null;
    }

    return $DocumentTypeModelCopyWith<$Res>(_value.docTypeDetail!, (value) {
      return _then(_value.copyWith(docTypeDetail: value) as $Val);
    });
  }

  /// Create a copy of ApprovalDocumentModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SimpleUserModelCopyWith<$Res> get drafter {
    return $SimpleUserModelCopyWith<$Res>(_value.drafter, (value) {
      return _then(_value.copyWith(drafter: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$ApprovalDocumentModelImplCopyWith<$Res>
    implements $ApprovalDocumentModelCopyWith<$Res> {
  factory _$$ApprovalDocumentModelImplCopyWith(
    _$ApprovalDocumentModelImpl value,
    $Res Function(_$ApprovalDocumentModelImpl) then,
  ) = __$$ApprovalDocumentModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    @JsonKey(readValue: _readId) int id,
    @JsonKey(readValue: _readStr) String docNumber,
    @JsonKey(readValue: _readStr) String title,
    @JsonKey(readValue: _readDocTypeId) int docType,
    String? docTypeName,
    String? categoryName,
    DocumentTypeModel? docTypeDetail,
    SimpleUserModel drafter,
    String? drafterName,
    int? drafterAssignment,
    String? departmentName,
    String? drafterAssignmentDesc,
    Map<String, dynamic> content,
    @JsonKey(readValue: _readStr) String status,
    String? statusDesc,
    int currentStep,
    @JsonKey(readValue: _readStr) String contentHash,
    String? pdfUrl,
    int attachmentCount,
    int observerCount,
    List<ApprovalAttachmentModel>? attachments,
    List<SimpleUserModel>? observers,
    List<ApprovalStepModel>? steps,
    @JsonKey(readValue: _readStr) String createdAt,
    String? submittedAt,
    String? completedAt,
  });

  @override
  $DocumentTypeModelCopyWith<$Res>? get docTypeDetail;
  @override
  $SimpleUserModelCopyWith<$Res> get drafter;
}

/// @nodoc
class __$$ApprovalDocumentModelImplCopyWithImpl<$Res>
    extends
        _$ApprovalDocumentModelCopyWithImpl<$Res, _$ApprovalDocumentModelImpl>
    implements _$$ApprovalDocumentModelImplCopyWith<$Res> {
  __$$ApprovalDocumentModelImplCopyWithImpl(
    _$ApprovalDocumentModelImpl _value,
    $Res Function(_$ApprovalDocumentModelImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of ApprovalDocumentModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? docNumber = null,
    Object? title = null,
    Object? docType = null,
    Object? docTypeName = freezed,
    Object? categoryName = freezed,
    Object? docTypeDetail = freezed,
    Object? drafter = null,
    Object? drafterName = freezed,
    Object? drafterAssignment = freezed,
    Object? departmentName = freezed,
    Object? drafterAssignmentDesc = freezed,
    Object? content = null,
    Object? status = null,
    Object? statusDesc = freezed,
    Object? currentStep = null,
    Object? contentHash = null,
    Object? pdfUrl = freezed,
    Object? attachmentCount = null,
    Object? observerCount = null,
    Object? attachments = freezed,
    Object? observers = freezed,
    Object? steps = freezed,
    Object? createdAt = null,
    Object? submittedAt = freezed,
    Object? completedAt = freezed,
  }) {
    return _then(
      _$ApprovalDocumentModelImpl(
        id: null == id
            ? _value.id
            : id // ignore: cast_nullable_to_non_nullable
                  as int,
        docNumber: null == docNumber
            ? _value.docNumber
            : docNumber // ignore: cast_nullable_to_non_nullable
                  as String,
        title: null == title
            ? _value.title
            : title // ignore: cast_nullable_to_non_nullable
                  as String,
        docType: null == docType
            ? _value.docType
            : docType // ignore: cast_nullable_to_non_nullable
                  as int,
        docTypeName: freezed == docTypeName
            ? _value.docTypeName
            : docTypeName // ignore: cast_nullable_to_non_nullable
                  as String?,
        categoryName: freezed == categoryName
            ? _value.categoryName
            : categoryName // ignore: cast_nullable_to_non_nullable
                  as String?,
        docTypeDetail: freezed == docTypeDetail
            ? _value.docTypeDetail
            : docTypeDetail // ignore: cast_nullable_to_non_nullable
                  as DocumentTypeModel?,
        drafter: null == drafter
            ? _value.drafter
            : drafter // ignore: cast_nullable_to_non_nullable
                  as SimpleUserModel,
        drafterName: freezed == drafterName
            ? _value.drafterName
            : drafterName // ignore: cast_nullable_to_non_nullable
                  as String?,
        drafterAssignment: freezed == drafterAssignment
            ? _value.drafterAssignment
            : drafterAssignment // ignore: cast_nullable_to_non_nullable
                  as int?,
        departmentName: freezed == departmentName
            ? _value.departmentName
            : departmentName // ignore: cast_nullable_to_non_nullable
                  as String?,
        drafterAssignmentDesc: freezed == drafterAssignmentDesc
            ? _value.drafterAssignmentDesc
            : drafterAssignmentDesc // ignore: cast_nullable_to_non_nullable
                  as String?,
        content: null == content
            ? _value._content
            : content // ignore: cast_nullable_to_non_nullable
                  as Map<String, dynamic>,
        status: null == status
            ? _value.status
            : status // ignore: cast_nullable_to_non_nullable
                  as String,
        statusDesc: freezed == statusDesc
            ? _value.statusDesc
            : statusDesc // ignore: cast_nullable_to_non_nullable
                  as String?,
        currentStep: null == currentStep
            ? _value.currentStep
            : currentStep // ignore: cast_nullable_to_non_nullable
                  as int,
        contentHash: null == contentHash
            ? _value.contentHash
            : contentHash // ignore: cast_nullable_to_non_nullable
                  as String,
        pdfUrl: freezed == pdfUrl
            ? _value.pdfUrl
            : pdfUrl // ignore: cast_nullable_to_non_nullable
                  as String?,
        attachmentCount: null == attachmentCount
            ? _value.attachmentCount
            : attachmentCount // ignore: cast_nullable_to_non_nullable
                  as int,
        observerCount: null == observerCount
            ? _value.observerCount
            : observerCount // ignore: cast_nullable_to_non_nullable
                  as int,
        attachments: freezed == attachments
            ? _value._attachments
            : attachments // ignore: cast_nullable_to_non_nullable
                  as List<ApprovalAttachmentModel>?,
        observers: freezed == observers
            ? _value._observers
            : observers // ignore: cast_nullable_to_non_nullable
                  as List<SimpleUserModel>?,
        steps: freezed == steps
            ? _value._steps
            : steps // ignore: cast_nullable_to_non_nullable
                  as List<ApprovalStepModel>?,
        createdAt: null == createdAt
            ? _value.createdAt
            : createdAt // ignore: cast_nullable_to_non_nullable
                  as String,
        submittedAt: freezed == submittedAt
            ? _value.submittedAt
            : submittedAt // ignore: cast_nullable_to_non_nullable
                  as String?,
        completedAt: freezed == completedAt
            ? _value.completedAt
            : completedAt // ignore: cast_nullable_to_non_nullable
                  as String?,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$ApprovalDocumentModelImpl implements _ApprovalDocumentModel {
  const _$ApprovalDocumentModelImpl({
    @JsonKey(readValue: _readId) required this.id,
    @JsonKey(readValue: _readStr) this.docNumber = '',
    @JsonKey(readValue: _readStr) this.title = '',
    @JsonKey(readValue: _readDocTypeId) required this.docType,
    this.docTypeName,
    this.categoryName,
    this.docTypeDetail,
    required this.drafter,
    this.drafterName,
    this.drafterAssignment,
    this.departmentName,
    this.drafterAssignmentDesc,
    final Map<String, dynamic> content = const {},
    @JsonKey(readValue: _readStr) this.status = 'draft',
    this.statusDesc,
    this.currentStep = 1,
    @JsonKey(readValue: _readStr) this.contentHash = '',
    this.pdfUrl,
    this.attachmentCount = 0,
    this.observerCount = 0,
    final List<ApprovalAttachmentModel>? attachments,
    final List<SimpleUserModel>? observers,
    final List<ApprovalStepModel>? steps,
    @JsonKey(readValue: _readStr) this.createdAt = '',
    this.submittedAt,
    this.completedAt,
  }) : _content = content,
       _attachments = attachments,
       _observers = observers,
       _steps = steps;

  factory _$ApprovalDocumentModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$ApprovalDocumentModelImplFromJson(json);

  @override
  @JsonKey(readValue: _readId)
  final int id;
  @override
  @JsonKey(readValue: _readStr)
  final String docNumber;
  @override
  @JsonKey(readValue: _readStr)
  final String title;
  @override
  @JsonKey(readValue: _readDocTypeId)
  final int docType;
  @override
  final String? docTypeName;
  @override
  final String? categoryName;
  @override
  final DocumentTypeModel? docTypeDetail;
  @override
  final SimpleUserModel drafter;
  @override
  final String? drafterName;
  @override
  final int? drafterAssignment;
  @override
  final String? departmentName;
  @override
  final String? drafterAssignmentDesc;
  final Map<String, dynamic> _content;
  @override
  @JsonKey()
  Map<String, dynamic> get content {
    if (_content is EqualUnmodifiableMapView) return _content;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_content);
  }

  @override
  @JsonKey(readValue: _readStr)
  final String status;
  // draft, pending, approved, rejected, cancelled
  @override
  final String? statusDesc;
  @override
  @JsonKey()
  final int currentStep;
  @override
  @JsonKey(readValue: _readStr)
  final String contentHash;
  @override
  final String? pdfUrl;
  @override
  @JsonKey()
  final int attachmentCount;
  @override
  @JsonKey()
  final int observerCount;
  final List<ApprovalAttachmentModel>? _attachments;
  @override
  List<ApprovalAttachmentModel>? get attachments {
    final value = _attachments;
    if (value == null) return null;
    if (_attachments is EqualUnmodifiableListView) return _attachments;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  final List<SimpleUserModel>? _observers;
  @override
  List<SimpleUserModel>? get observers {
    final value = _observers;
    if (value == null) return null;
    if (_observers is EqualUnmodifiableListView) return _observers;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  final List<ApprovalStepModel>? _steps;
  @override
  List<ApprovalStepModel>? get steps {
    final value = _steps;
    if (value == null) return null;
    if (_steps is EqualUnmodifiableListView) return _steps;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  @override
  @JsonKey(readValue: _readStr)
  final String createdAt;
  @override
  final String? submittedAt;
  @override
  final String? completedAt;

  @override
  String toString() {
    return 'ApprovalDocumentModel(id: $id, docNumber: $docNumber, title: $title, docType: $docType, docTypeName: $docTypeName, categoryName: $categoryName, docTypeDetail: $docTypeDetail, drafter: $drafter, drafterName: $drafterName, drafterAssignment: $drafterAssignment, departmentName: $departmentName, drafterAssignmentDesc: $drafterAssignmentDesc, content: $content, status: $status, statusDesc: $statusDesc, currentStep: $currentStep, contentHash: $contentHash, pdfUrl: $pdfUrl, attachmentCount: $attachmentCount, observerCount: $observerCount, attachments: $attachments, observers: $observers, steps: $steps, createdAt: $createdAt, submittedAt: $submittedAt, completedAt: $completedAt)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ApprovalDocumentModelImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.docNumber, docNumber) ||
                other.docNumber == docNumber) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.docType, docType) || other.docType == docType) &&
            (identical(other.docTypeName, docTypeName) ||
                other.docTypeName == docTypeName) &&
            (identical(other.categoryName, categoryName) ||
                other.categoryName == categoryName) &&
            (identical(other.docTypeDetail, docTypeDetail) ||
                other.docTypeDetail == docTypeDetail) &&
            (identical(other.drafter, drafter) || other.drafter == drafter) &&
            (identical(other.drafterName, drafterName) ||
                other.drafterName == drafterName) &&
            (identical(other.drafterAssignment, drafterAssignment) ||
                other.drafterAssignment == drafterAssignment) &&
            (identical(other.departmentName, departmentName) ||
                other.departmentName == departmentName) &&
            (identical(other.drafterAssignmentDesc, drafterAssignmentDesc) ||
                other.drafterAssignmentDesc == drafterAssignmentDesc) &&
            const DeepCollectionEquality().equals(other._content, _content) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.statusDesc, statusDesc) ||
                other.statusDesc == statusDesc) &&
            (identical(other.currentStep, currentStep) ||
                other.currentStep == currentStep) &&
            (identical(other.contentHash, contentHash) ||
                other.contentHash == contentHash) &&
            (identical(other.pdfUrl, pdfUrl) || other.pdfUrl == pdfUrl) &&
            (identical(other.attachmentCount, attachmentCount) ||
                other.attachmentCount == attachmentCount) &&
            (identical(other.observerCount, observerCount) ||
                other.observerCount == observerCount) &&
            const DeepCollectionEquality().equals(
              other._attachments,
              _attachments,
            ) &&
            const DeepCollectionEquality().equals(
              other._observers,
              _observers,
            ) &&
            const DeepCollectionEquality().equals(other._steps, _steps) &&
            (identical(other.createdAt, createdAt) ||
                other.createdAt == createdAt) &&
            (identical(other.submittedAt, submittedAt) ||
                other.submittedAt == submittedAt) &&
            (identical(other.completedAt, completedAt) ||
                other.completedAt == completedAt));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hashAll([
    runtimeType,
    id,
    docNumber,
    title,
    docType,
    docTypeName,
    categoryName,
    docTypeDetail,
    drafter,
    drafterName,
    drafterAssignment,
    departmentName,
    drafterAssignmentDesc,
    const DeepCollectionEquality().hash(_content),
    status,
    statusDesc,
    currentStep,
    contentHash,
    pdfUrl,
    attachmentCount,
    observerCount,
    const DeepCollectionEquality().hash(_attachments),
    const DeepCollectionEquality().hash(_observers),
    const DeepCollectionEquality().hash(_steps),
    createdAt,
    submittedAt,
    completedAt,
  ]);

  /// Create a copy of ApprovalDocumentModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ApprovalDocumentModelImplCopyWith<_$ApprovalDocumentModelImpl>
  get copyWith =>
      __$$ApprovalDocumentModelImplCopyWithImpl<_$ApprovalDocumentModelImpl>(
        this,
        _$identity,
      );

  @override
  Map<String, dynamic> toJson() {
    return _$$ApprovalDocumentModelImplToJson(this);
  }
}

abstract class _ApprovalDocumentModel implements ApprovalDocumentModel {
  const factory _ApprovalDocumentModel({
    @JsonKey(readValue: _readId) required final int id,
    @JsonKey(readValue: _readStr) final String docNumber,
    @JsonKey(readValue: _readStr) final String title,
    @JsonKey(readValue: _readDocTypeId) required final int docType,
    final String? docTypeName,
    final String? categoryName,
    final DocumentTypeModel? docTypeDetail,
    required final SimpleUserModel drafter,
    final String? drafterName,
    final int? drafterAssignment,
    final String? departmentName,
    final String? drafterAssignmentDesc,
    final Map<String, dynamic> content,
    @JsonKey(readValue: _readStr) final String status,
    final String? statusDesc,
    final int currentStep,
    @JsonKey(readValue: _readStr) final String contentHash,
    final String? pdfUrl,
    final int attachmentCount,
    final int observerCount,
    final List<ApprovalAttachmentModel>? attachments,
    final List<SimpleUserModel>? observers,
    final List<ApprovalStepModel>? steps,
    @JsonKey(readValue: _readStr) final String createdAt,
    final String? submittedAt,
    final String? completedAt,
  }) = _$ApprovalDocumentModelImpl;

  factory _ApprovalDocumentModel.fromJson(Map<String, dynamic> json) =
      _$ApprovalDocumentModelImpl.fromJson;

  @override
  @JsonKey(readValue: _readId)
  int get id;
  @override
  @JsonKey(readValue: _readStr)
  String get docNumber;
  @override
  @JsonKey(readValue: _readStr)
  String get title;
  @override
  @JsonKey(readValue: _readDocTypeId)
  int get docType;
  @override
  String? get docTypeName;
  @override
  String? get categoryName;
  @override
  DocumentTypeModel? get docTypeDetail;
  @override
  SimpleUserModel get drafter;
  @override
  String? get drafterName;
  @override
  int? get drafterAssignment;
  @override
  String? get departmentName;
  @override
  String? get drafterAssignmentDesc;
  @override
  Map<String, dynamic> get content;
  @override
  @JsonKey(readValue: _readStr)
  String get status; // draft, pending, approved, rejected, cancelled
  @override
  String? get statusDesc;
  @override
  int get currentStep;
  @override
  @JsonKey(readValue: _readStr)
  String get contentHash;
  @override
  String? get pdfUrl;
  @override
  int get attachmentCount;
  @override
  int get observerCount;
  @override
  List<ApprovalAttachmentModel>? get attachments;
  @override
  List<SimpleUserModel>? get observers;
  @override
  List<ApprovalStepModel>? get steps;
  @override
  @JsonKey(readValue: _readStr)
  String get createdAt;
  @override
  String? get submittedAt;
  @override
  String? get completedAt;

  /// Create a copy of ApprovalDocumentModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ApprovalDocumentModelImplCopyWith<_$ApprovalDocumentModelImpl>
  get copyWith => throw _privateConstructorUsedError;
}

ApprovalDocumentListResponse _$ApprovalDocumentListResponseFromJson(
  Map<String, dynamic> json,
) {
  return _ApprovalDocumentListResponse.fromJson(json);
}

/// @nodoc
mixin _$ApprovalDocumentListResponse {
  int get count => throw _privateConstructorUsedError;
  String? get next => throw _privateConstructorUsedError;
  String? get previous => throw _privateConstructorUsedError;
  List<ApprovalDocumentModel> get results => throw _privateConstructorUsedError;

  /// Serializes this ApprovalDocumentListResponse to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ApprovalDocumentListResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ApprovalDocumentListResponseCopyWith<ApprovalDocumentListResponse>
  get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ApprovalDocumentListResponseCopyWith<$Res> {
  factory $ApprovalDocumentListResponseCopyWith(
    ApprovalDocumentListResponse value,
    $Res Function(ApprovalDocumentListResponse) then,
  ) =
      _$ApprovalDocumentListResponseCopyWithImpl<
        $Res,
        ApprovalDocumentListResponse
      >;
  @useResult
  $Res call({
    int count,
    String? next,
    String? previous,
    List<ApprovalDocumentModel> results,
  });
}

/// @nodoc
class _$ApprovalDocumentListResponseCopyWithImpl<
  $Res,
  $Val extends ApprovalDocumentListResponse
>
    implements $ApprovalDocumentListResponseCopyWith<$Res> {
  _$ApprovalDocumentListResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ApprovalDocumentListResponse
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
                      as List<ApprovalDocumentModel>,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$ApprovalDocumentListResponseImplCopyWith<$Res>
    implements $ApprovalDocumentListResponseCopyWith<$Res> {
  factory _$$ApprovalDocumentListResponseImplCopyWith(
    _$ApprovalDocumentListResponseImpl value,
    $Res Function(_$ApprovalDocumentListResponseImpl) then,
  ) = __$$ApprovalDocumentListResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int count,
    String? next,
    String? previous,
    List<ApprovalDocumentModel> results,
  });
}

/// @nodoc
class __$$ApprovalDocumentListResponseImplCopyWithImpl<$Res>
    extends
        _$ApprovalDocumentListResponseCopyWithImpl<
          $Res,
          _$ApprovalDocumentListResponseImpl
        >
    implements _$$ApprovalDocumentListResponseImplCopyWith<$Res> {
  __$$ApprovalDocumentListResponseImplCopyWithImpl(
    _$ApprovalDocumentListResponseImpl _value,
    $Res Function(_$ApprovalDocumentListResponseImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of ApprovalDocumentListResponse
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
      _$ApprovalDocumentListResponseImpl(
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
                  as List<ApprovalDocumentModel>,
      ),
    );
  }
}

/// @nodoc

@JsonSerializable(fieldRename: FieldRename.snake)
class _$ApprovalDocumentListResponseImpl
    implements _ApprovalDocumentListResponse {
  const _$ApprovalDocumentListResponseImpl({
    this.count = 0,
    this.next,
    this.previous,
    final List<ApprovalDocumentModel> results = const [],
  }) : _results = results;

  factory _$ApprovalDocumentListResponseImpl.fromJson(
    Map<String, dynamic> json,
  ) => _$$ApprovalDocumentListResponseImplFromJson(json);

  @override
  @JsonKey()
  final int count;
  @override
  final String? next;
  @override
  final String? previous;
  final List<ApprovalDocumentModel> _results;
  @override
  @JsonKey()
  List<ApprovalDocumentModel> get results {
    if (_results is EqualUnmodifiableListView) return _results;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_results);
  }

  @override
  String toString() {
    return 'ApprovalDocumentListResponse(count: $count, next: $next, previous: $previous, results: $results)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ApprovalDocumentListResponseImpl &&
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

  /// Create a copy of ApprovalDocumentListResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ApprovalDocumentListResponseImplCopyWith<
    _$ApprovalDocumentListResponseImpl
  >
  get copyWith =>
      __$$ApprovalDocumentListResponseImplCopyWithImpl<
        _$ApprovalDocumentListResponseImpl
      >(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ApprovalDocumentListResponseImplToJson(this);
  }
}

abstract class _ApprovalDocumentListResponse
    implements ApprovalDocumentListResponse {
  const factory _ApprovalDocumentListResponse({
    final int count,
    final String? next,
    final String? previous,
    final List<ApprovalDocumentModel> results,
  }) = _$ApprovalDocumentListResponseImpl;

  factory _ApprovalDocumentListResponse.fromJson(Map<String, dynamic> json) =
      _$ApprovalDocumentListResponseImpl.fromJson;

  @override
  int get count;
  @override
  String? get next;
  @override
  String? get previous;
  @override
  List<ApprovalDocumentModel> get results;

  /// Create a copy of ApprovalDocumentListResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ApprovalDocumentListResponseImplCopyWith<
    _$ApprovalDocumentListResponseImpl
  >
  get copyWith => throw _privateConstructorUsedError;
}
