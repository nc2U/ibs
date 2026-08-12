import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api/api_client.dart';
import '../storage/token_storage.dart';

/// TokenStorage 프로바이더 (싱글톤)
final tokenStorageProvider = Provider<TokenStorage>((ref) {
  return TokenStorage();
});

/// Dio 프로바이더 (AuthInterceptor 포함)
final dioProvider = Provider<Dio>((ref) {
  final tokenStorage = ref.watch(tokenStorageProvider);
  return createDio(tokenStorage);
});
