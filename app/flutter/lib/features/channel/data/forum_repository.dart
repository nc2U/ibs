import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/providers/dio_provider.dart';
import 'models/forum_model.dart';

final forumRepositoryProvider = Provider<ForumRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return ForumRepository(dio);
});

class ForumRepository {
  final Dio _dio;
  ForumRepository(this._dio);

  /// 게시판 목록 조회
  Future<List<ForumModel>> fetchForums({
    int? projectId,
    String? projectSlug,
  }) async {
    try {
      final queryParams = <String, dynamic>{};
      if (projectSlug != null && projectSlug.isNotEmpty) {
        queryParams['project__slug'] = projectSlug;
      }
      final response = await _dio.get('/api/v1/forum/', queryParameters: queryParams);
      final list = (response.data['results'] ?? response.data) as List<dynamic>;
      return list.map((e) => ForumModel.fromJson(e as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '게시판 목록을 불러오지 못했습니다.');
    }
  }

  /// 카테고리 목록 조회
  Future<List<PostCategoryModel>> fetchCategories(int forumId) async {
    try {
      final response = await _dio.get('/api/v1/post-category/', queryParameters: {'forum': forumId});
      final list = (response.data['results'] ?? response.data) as List<dynamic>;
      return list.map((e) => PostCategoryModel.fromJson(e as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '카테고리 목록을 불러오지 못했습니다.');
    }
  }

  /// 게시글 목록 조회
  Future<PostListResponse> fetchPosts({
    int? forumId,
    int? categoryId,
    int? projectId,
    String? projectSlug,
    String? search,
    int page = 1,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'page': page,
      };
      if (forumId != null) {
        queryParams['forum'] = forumId;
      }
      if (categoryId != null) {
        queryParams['category'] = categoryId;
      }
      if (projectId != null) {
        queryParams['forum__project'] = projectId;
      } else if (projectSlug != null && projectSlug.isNotEmpty) {
        queryParams['forum__project__slug'] = projectSlug;
      }
      if (search != null && search.trim().isNotEmpty) {
        queryParams['search'] = search.trim();
      }

      final response = await _dio.get('/api/v1/post/', queryParameters: queryParams);
      return PostListResponse.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '게시글 목록을 불러오지 못했습니다.');
    }
  }

  /// 게시글 상세 조회
  Future<PostModel> fetchPostDetail(int id) async {
    try {
      final response = await _dio.get('/api/v1/post/$id/');
      return PostModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '게시글을 불러오지 못했습니다.');
    }
  }

  /// 조회수 증가
  Future<void> hitPost(int id) async {
    try {
      await _dio.post('/api/v1/post/$id/hit/');
    } catch (_) {}
  }

  /// 좋아요
  Future<void> likePost(int id) async {
    try {
      await _dio.patch('/api/v1/post-like/$id/');
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '좋아요 처리에 실패했습니다.');
    }
  }

  /// 비추천
  Future<void> blamePost(int id) async {
    try {
      await _dio.patch('/api/v1/post-blame/$id/');
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '비추천 처리에 실패했습니다.');
    }
  }

  /// 게시글 등록
  Future<PostModel> createPost({
    required int forumId,
    int? categoryId,
    required String title,
    String content = '',
    bool isNotice = false,
    bool isFaq = false,
    List<PlatformFile>? newFiles,
  }) async {
    try {
      if (newFiles == null || newFiles.isEmpty) {
        final data = {
          'forum': forumId,
          if (categoryId != null) 'category': categoryId,
          'title': title,
          'content': content,
          'is_notice': isNotice,
          'is_faq': isFaq,
        };
        final response = await _dio.post('/api/v1/post/', data: data);
        return PostModel.fromJson(response.data as Map<String, dynamic>);
      }

      final formData = FormData();
      formData.fields.add(MapEntry('forum', forumId.toString()));
      if (categoryId != null) {
        formData.fields.add(MapEntry('category', categoryId.toString()));
      }
      formData.fields.add(MapEntry('title', title));
      formData.fields.add(MapEntry('content', content));
      formData.fields.add(MapEntry('is_notice', isNotice ? 'true' : 'false'));
      formData.fields.add(MapEntry('is_faq', isFaq ? 'true' : 'false'));

      for (var pf in newFiles) {
        if (pf.bytes != null) {
          formData.files.add(
            MapEntry(
              'newFiles',
              MultipartFile.fromBytes(pf.bytes!, filename: pf.name),
            ),
          );
        } else if (pf.path != null) {
          formData.files.add(
            MapEntry(
              'newFiles',
              await MultipartFile.fromFile(pf.path!, filename: pf.name),
            ),
          );
        }
      }

      final response = await _dio.post(
        '/api/v1/post/',
        data: formData,
        options: Options(contentType: 'multipart/form-data'),
      );
      return PostModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '게시글 등록에 실패했습니다.');
    }
  }

  /// 게시글 수정
  Future<PostModel> updatePost({
    required int id,
    int? forumId,
    int? categoryId,
    required String title,
    String content = '',
    bool isNotice = false,
    bool isFaq = false,
    List<PlatformFile>? newFiles,
    List<int>? deleteFilePks,
  }) async {
    try {
      final formData = FormData();
      if (forumId != null) {
        formData.fields.add(MapEntry('forum', forumId.toString()));
      }
      if (categoryId != null) {
        formData.fields.add(MapEntry('category', categoryId.toString()));
      }
      formData.fields.add(MapEntry('title', title));
      formData.fields.add(MapEntry('content', content));
      formData.fields.add(MapEntry('is_notice', isNotice ? 'true' : 'false'));
      formData.fields.add(MapEntry('is_faq', isFaq ? 'true' : 'false'));

      if (deleteFilePks != null && deleteFilePks.isNotEmpty) {
        for (var pk in deleteFilePks) {
          formData.fields.add(MapEntry('del_file', pk.toString()));
        }
      }

      if (newFiles != null && newFiles.isNotEmpty) {
        for (var pf in newFiles) {
          if (pf.bytes != null) {
            formData.files.add(
              MapEntry(
                'newFiles',
                MultipartFile.fromBytes(pf.bytes!, filename: pf.name),
              ),
            );
          } else if (pf.path != null) {
            formData.files.add(
              MapEntry(
                'newFiles',
                await MultipartFile.fromFile(pf.path!, filename: pf.name),
              ),
            );
          }
        }
      }

      final response = await _dio.patch(
        '/api/v1/post/$id/',
        data: formData,
        options: Options(contentType: 'multipart/form-data'),
      );
      return PostModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '게시글 수정에 실패했습니다.');
    }
  }

  /// 게시글 삭제
  Future<void> deletePost(int id) async {
    try {
      await _dio.delete('/api/v1/post/$id/');
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '게시글 삭제에 실패했습니다.');
    }
  }

  /// 댓글 목록 조회
  Future<List<PostCommentModel>> fetchComments({
    required int postId,
    int page = 1,
  }) async {
    try {
      final response = await _dio.get(
        '/api/v1/comment/',
        queryParameters: {
          'post': postId,
          'is_comment': 'true',
          'page': page,
        },
      );
      final list = (response.data['results'] ?? response.data) as List<dynamic>;
      return list
          .whereType<Map<String, dynamic>>()
          .map((e) => PostCommentModel.fromJson(e))
          .toList();
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '댓글 목록을 불러오지 못했습니다.');
    }
  }

  /// 댓글 등록
  Future<PostCommentModel> createComment({
    required int postId,
    required String content,
    int? parent,
    String? projectSlug,
    int? projectId,
  }) async {
    try {
      final queryParams = <String, dynamic>{};
      if (projectSlug != null && projectSlug.isNotEmpty) {
        queryParams['project'] = projectSlug;
      } else if (projectId != null) {
        queryParams['project'] = projectId;
      }
      final data = {
        'post': postId,
        'content': content,
        if (parent != null) 'parent': parent,
      };
      final response = await _dio.post(
        '/api/v1/comment/',
        data: data,
        queryParameters: queryParams.isNotEmpty ? queryParams : null,
      );
      return PostCommentModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '댓글 등록에 실패했습니다.');
    }
  }

  /// 댓글 삭제
  Future<void> deleteComment(int id) async {
    try {
      await _dio.delete('/api/v1/comment/$id/');
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '댓글 삭제에 실패했습니다.');
    }
  }
}
