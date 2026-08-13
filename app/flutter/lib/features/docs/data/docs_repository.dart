import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/providers/dio_provider.dart';
import 'models/docs_model.dart';

final docsRepositoryProvider = Provider<DocsRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return DocsRepository(dio);
});

class DocsRepository {
  final Dio _dio;
  DocsRepository(this._dio);

  /// 문서 목록 조회
  Future<DocumentListResponseModel> fetchDocuments({
    int? issueProject,
    String? docType,
    int? category,
    String? search,
    int page = 1,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'page': page,
      };
      if (issueProject != null) {
        queryParams['issue_project'] = issueProject;
      }
      if (docType != null && docType.isNotEmpty) {
        queryParams['doc_type'] = docType;
      }
      if (category != null) {
        queryParams['category'] = category;
      }
      if (search != null && search.trim().isNotEmpty) {
        queryParams['search'] = search.trim();
      }

      final response = await _dio.get('/api/v1/docs/', queryParameters: queryParams);
      return DocumentListResponseModel.fromJson(response.data);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '문서 목록을 불러오지 못했습니다.');
    }
  }

  /// 카테고리 목록 조회
  Future<List<DocCategoryModel>> fetchCategories({String? docType}) async {
    try {
      final queryParams = <String, dynamic>{};
      if (docType != null && docType.isNotEmpty) {
        queryParams['doc_type'] = docType;
      }
      final response = await _dio.get('/api/v1/category/', queryParameters: queryParams);
      final results = response.data['results'] as List<dynamic>? ?? [];
      return results.map((e) => DocCategoryModel.fromJson(e)).toList();
    } on DioException {
      return [];
    }
  }

  /// 문서 상세 조회
  Future<DocumentModel> fetchDocumentDetail(int id) async {
    try {
      final response = await _dio.get('/api/v1/docs/$id/');
      return DocumentModel.fromJson(response.data);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '문서 상세 정보를 불러오지 못했습니다.');
    }
  }

  /// 문서 신규 생성
  Future<DocumentModel> createDocument({
    required int issueProjectId,
    required String title,
    int? categoryId,
    String? executionDate,
    String? description,
    bool isSecret = false,
  }) async {
    try {
      final body = <String, dynamic>{
        'issue_project': issueProjectId,
        'title': title,
        'is_secret': isSecret,
      };
      if (categoryId != null) body['category'] = categoryId;
      if (executionDate != null && executionDate.isNotEmpty) {
        body['execution_date'] = executionDate;
      }
      if (description != null) body['description'] = description;

      final response = await _dio.post('/api/v1/docs/', data: body);
      return DocumentModel.fromJson(response.data);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '문서 등록에 실패했습니다.');
    }
  }

  /// 문서 수정
  Future<DocumentModel> updateDocument({
    required int id,
    required String title,
    int? categoryId,
    String? executionDate,
    String? description,
    bool? isSecret,
  }) async {
    try {
      final body = <String, dynamic>{
        'title': title,
      };
      if (categoryId != null) body['category'] = categoryId;
      if (executionDate != null) body['execution_date'] = executionDate;
      if (description != null) body['description'] = description;
      if (isSecret != null) body['is_secret'] = isSecret;

      final response = await _dio.patch('/api/v1/docs/$id/', data: body);
      return DocumentModel.fromJson(response.data);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '문서 수정에 실패했습니다.');
    }
  }

  /// 문서 삭제
  Future<void> deleteDocument(int id) async {
    try {
      await _dio.delete('/api/v1/docs/$id/');
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '문서 삭제에 실패했습니다.');
    }
  }
}
