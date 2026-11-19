import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
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
        'ordering': '-is_pinned,-created',
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
  Future<List<DocCategoryModel>> fetchCategories({String? docType, bool activeOnly = true}) async {
    try {
      final queryParams = <String, dynamic>{'limit': 200};
      if (docType != null && docType.isNotEmpty) {
        queryParams['doc_type'] = docType;
      }
      if (activeOnly) {
        queryParams['active'] = true;
      }
      final response = await _dio.get('/api/v1/category/', queryParameters: queryParams);
      final data = response.data;
      final List<dynamic> results = (data is List)
          ? data
          : (data is Map && data['results'] is List
              ? data['results'] as List
              : []);
      return results.map((e) => DocCategoryModel.fromJson(e as Map<String, dynamic>)).toList();
    } on DioException {
      return [];
    }
  }

  /// 소송 사건 목록 조회 (옵션 드롭다운용)
  Future<List<SuitCaseOptionModel>> fetchSuitCases({int? issueProject}) async {
    final queryParams = <String, dynamic>{};
    if (issueProject != null) {
      queryParams['issue_project'] = issueProject;
    }
    try {
      final response = await _dio.get('/api/v1/all-suitcase/', queryParameters: queryParams);
      final list = (response.data is List) ? (response.data as List) : (response.data['results'] as List? ?? []);
      return list.map((e) => SuitCaseOptionModel.fromJson(e as Map<String, dynamic>)).toList();
    } on DioException {
      try {
        final response = await _dio.get('/api/v1/suitcase/', queryParameters: queryParams);
        final list = (response.data is List) ? (response.data as List) : (response.data['results'] as List? ?? []);
        return list.map((e) => SuitCaseOptionModel.fromJson(e as Map<String, dynamic>)).toList();
      } catch (_) {
        return [];
      }
    }
  }

  /// 문서 조회수 증가
  Future<void> hitDocument(int id) async {
    try {
      await _dio.post('/api/v1/docs/$id/hit/');
    } catch (_) {
      // 조회수 증가 실패는 무시
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

  /// 문서 신규 생성 (FormData 멀티파트 지원)
  Future<DocumentModel> createDocument({
    required int issueProjectId,
    required String title,
    String docType = '1',
    int? categoryId,
    int? lawsuitId,
    String? executionDate,
    String? description,
    String securityLevel = '3',
    List<PlatformFile>? newFiles,
    List<String>? newLinks,
  }) async {
    try {
      final formData = FormData();
      formData.fields.add(MapEntry('issue_project', issueProjectId.toString()));
      formData.fields.add(MapEntry('doc_type', docType));
      formData.fields.add(MapEntry('title', title));
      formData.fields.add(MapEntry('security_level', securityLevel));
      if (categoryId != null) {
        formData.fields.add(MapEntry('category', categoryId.toString()));
      }
      if (lawsuitId != null) {
        formData.fields.add(MapEntry('lawsuit', lawsuitId.toString()));
      }
      if (executionDate != null && executionDate.isNotEmpty) {
        formData.fields.add(MapEntry('execution_date', executionDate));
      }
      if (description != null) {
        formData.fields.add(MapEntry('description', description));
      }

      // 새 링크 목록
      if (newLinks != null && newLinks.isNotEmpty) {
        for (final link in newLinks) {
          if (link.trim().isNotEmpty) {
            formData.fields.add(MapEntry('newLinks', link.trim()));
          }
        }
      }

      // 새 파일 목록
      if (newFiles != null && newFiles.isNotEmpty) {
        for (final file in newFiles) {
          if (file.bytes != null) {
            formData.files.add(
              MapEntry(
                'newFiles',
                MultipartFile.fromBytes(file.bytes!, filename: file.name),
              ),
            );
          } else if (file.path != null) {
            formData.files.add(
              MapEntry(
                'newFiles',
                await MultipartFile.fromFile(file.path!, filename: file.name),
              ),
            );
          }
        }
      }

      final response = await _dio.post('/api/v1/docs/', data: formData);
      return DocumentModel.fromJson(response.data);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '문서 등록에 실패했습니다.');
    }
  }

  /// 문서 수정 (FormData 멀티파트 지원)
  Future<DocumentModel> updateDocument({
    required int id,
    required String title,
    String? docType,
    int? categoryId,
    int? lawsuitId,
    String? executionDate,
    String? description,
    String? securityLevel,
    List<PlatformFile>? newFiles,
    List<String>? newLinks,
    List<int>? deleteFilePks,
    List<int>? deleteLinkPks,
  }) async {
    try {
      final formData = FormData();
      formData.fields.add(MapEntry('title', title));
      if (docType != null && docType.isNotEmpty) {
        formData.fields.add(MapEntry('doc_type', docType));
      }
      formData.fields.add(MapEntry('category', categoryId?.toString() ?? ''));
      formData.fields.add(MapEntry('lawsuit', lawsuitId?.toString() ?? ''));
      if (executionDate != null) {
        formData.fields.add(MapEntry('execution_date', executionDate));
      }
      if (description != null) {
        formData.fields.add(MapEntry('description', description));
      }
      if (securityLevel != null) {
        formData.fields.add(MapEntry('security_level', securityLevel));
      }

      // 새 링크 목록
      if (newLinks != null && newLinks.isNotEmpty) {
        for (final link in newLinks) {
          if (link.trim().isNotEmpty) {
            formData.fields.add(MapEntry('newLinks', link.trim()));
          }
        }
      }

      // 삭제할 링크 목록
      if (deleteLinkPks != null && deleteLinkPks.isNotEmpty) {
        for (final pk in deleteLinkPks) {
          formData.fields.add(
            MapEntry('links', jsonEncode({'pk': pk, 'del': true})),
          );
        }
      }

      // 새 파일 목록
      if (newFiles != null && newFiles.isNotEmpty) {
        for (final file in newFiles) {
          if (file.bytes != null) {
            formData.files.add(
              MapEntry(
                'newFiles',
                MultipartFile.fromBytes(file.bytes!, filename: file.name),
              ),
            );
          } else if (file.path != null) {
            formData.files.add(
              MapEntry(
                'newFiles',
                await MultipartFile.fromFile(file.path!, filename: file.name),
              ),
            );
          }
        }
      }

      // 삭제할 파일 목록
      if (deleteFilePks != null && deleteFilePks.isNotEmpty) {
        for (final pk in deleteFilePks) {
          formData.fields.add(
            MapEntry('files', jsonEncode({'pk': pk, 'del': true})),
          );
        }
      }

      final response = await _dio.patch('/api/v1/docs/$id/', data: formData);
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
