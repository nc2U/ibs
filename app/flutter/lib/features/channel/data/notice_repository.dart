import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/providers/dio_provider.dart';
import 'models/notice_model.dart';

final noticeRepositoryProvider = Provider<NoticeRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return NoticeRepository(dio);
});

class NoticeRepository {
  final Dio _dio;
  NoticeRepository(this._dio);

  /// 공지사항 목록 조회
  Future<NoticeListResponse> fetchNotices({
    int? project,
    String? projectSlug,
    String? search,
    int page = 1,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'page': page,
      };
      if (project != null) {
        queryParams['project'] = project;
      } else if (projectSlug != null && projectSlug.isNotEmpty) {
        queryParams['project__slug'] = projectSlug;
      }
      if (search != null && search.trim().isNotEmpty) {
        queryParams['search'] = search.trim();
      }

      final response = await _dio.get('/api/v1/news/', queryParameters: queryParams);
      return NoticeListResponse.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '공지사항 목록을 불러오지 못했습니다.');
    }
  }

  /// 공지사항 상세 조회
  Future<NoticeModel> fetchNoticeDetail(int id) async {
    try {
      final response = await _dio.get('/api/v1/news/$id/');
      return NoticeModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '공지사항을 불러오지 못했습니다.');
    }
  }

  /// 공지사항 생성
  Future<NoticeModel> createNotice({
    required int projectId,
    required String title,
    String summary = '',
    String content = '',
    bool isImportant = false,
    List<PlatformFile>? newFiles,
  }) async {
    try {
      if (newFiles == null || newFiles.isEmpty) {
        final data = {
          'project': projectId,
          'title': title,
          'summary': summary,
          'content': content,
          'is_important': isImportant,
        };
        final response = await _dio.post('/api/v1/news/', data: data);
        return NoticeModel.fromJson(response.data as Map<String, dynamic>);
      }

      final formData = FormData();
      formData.fields.add(MapEntry('project', projectId.toString()));
      formData.fields.add(MapEntry('title', title));
      formData.fields.add(MapEntry('summary', summary));
      formData.fields.add(MapEntry('content', content));
      formData.fields.add(MapEntry('is_important', isImportant ? 'true' : 'false'));

      for (var pf in newFiles) {
        if (pf.bytes != null) {
          formData.files.add(
            MapEntry(
              'files',
              MultipartFile.fromBytes(pf.bytes!, filename: pf.name),
            ),
          );
        } else if (pf.path != null) {
          formData.files.add(
            MapEntry(
              'files',
              await MultipartFile.fromFile(pf.path!, filename: pf.name),
            ),
          );
        }
      }

      final response = await _dio.post(
        '/api/v1/news/',
        data: formData,
        options: Options(contentType: 'multipart/form-data'),
      );
      return NoticeModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '공지사항 등록에 실패했습니다.');
    }
  }

  /// 공지사항 수정
  Future<NoticeModel> updateNotice({
    required int id,
    int? projectId,
    required String title,
    String summary = '',
    String content = '',
    bool isImportant = false,
    List<PlatformFile>? newFiles,
    List<int>? deleteFilePks,
  }) async {
    try {
      final formData = FormData();
      if (projectId != null) {
        formData.fields.add(MapEntry('project', projectId.toString()));
      }
      formData.fields.add(MapEntry('title', title));
      formData.fields.add(MapEntry('summary', summary));
      formData.fields.add(MapEntry('content', content));
      formData.fields.add(MapEntry('is_important', isImportant ? 'true' : 'false'));

      if (deleteFilePks != null && deleteFilePks.isNotEmpty) {
        for (var pk in deleteFilePks) {
          formData.fields.add(MapEntry('del_files', pk.toString()));
        }
      }

      if (newFiles != null) {
        for (var pf in newFiles) {
          if (pf.bytes != null) {
            formData.files.add(
              MapEntry(
                'files',
                MultipartFile.fromBytes(pf.bytes!, filename: pf.name),
              ),
            );
          } else if (pf.path != null) {
            formData.files.add(
              MapEntry(
                'files',
                await MultipartFile.fromFile(pf.path!, filename: pf.name),
              ),
            );
          }
        }
      }

      final response = await _dio.patch(
        '/api/v1/news/$id/',
        data: formData,
        options: Options(contentType: 'multipart/form-data'),
      );
      return NoticeModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '공지사항 수정에 실패했습니다.');
    }
  }

  /// 공지사항 삭제
  Future<void> deleteNotice(int id) async {
    try {
      await _dio.delete('/api/v1/news/$id/');
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '공지사항 삭제에 실패했습니다.');
    }
  }

  /// 공지사항 댓글 등록
  Future<NoticeCommentModel> createComment({
    required int newsId,
    required String content,
    int? parent,
  }) async {
    try {
      final data = <String, dynamic>{
        'news': newsId,
        'content': content,
      };
      if (parent != null) {
        data['parent'] = parent;
      }
      final response = await _dio.post('/api/v1/news-comment/', data: data);
      return NoticeCommentModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '댓글 등록에 실패했습니다.');
    }
  }

  /// 공지사항 댓글 삭제
  Future<void> deleteComment(int commentId) async {
    try {
      await _dio.delete('/api/v1/news-comment/$commentId/');
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '댓글 삭제에 실패했습니다.');
    }
  }
}
