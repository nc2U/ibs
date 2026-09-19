import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SharePayload {
  final List<PlatformFile> files;
  final List<String> links;
  final String? defaultTitle;

  const SharePayload({
    this.files = const [],
    this.links = const [],
    this.defaultTitle,
  });

  bool get isEmpty => files.isEmpty && links.isEmpty;
  bool get isNotEmpty => !isEmpty;
}

class SharePayloadNotifier extends StateNotifier<SharePayload?> {
  SharePayloadNotifier() : super(null);

  void setPayload(SharePayload payload) {
    if (payload.isNotEmpty) {
      debugPrint('📥 [SharePayloadProvider] setPayload: files=${payload.files.length}, links=${payload.links.length}');
      state = payload;
    }
  }

  void setFromPath(String rawPath) {
    var cleanPath = rawPath;
    if (cleanPath.startsWith('file://')) {
      cleanPath = cleanPath.substring(7);
    }
    try {
      cleanPath = Uri.decodeFull(cleanPath);
    } catch (_) {
      try {
        cleanPath = Uri.decodeComponent(cleanPath);
      } catch (_) {}
    }

    debugPrint('📥 [SharePayloadProvider] setFromPath: raw=$rawPath, clean=$cleanPath');

    if (cleanPath.startsWith('http://') || cleanPath.startsWith('https://')) {
      state = SharePayload(
        links: [cleanPath],
        defaultTitle: '웹 링크 공유 문서',
      );
      return;
    }

    try {
      final file = File(cleanPath);
      final fileName = cleanPath.split(Platform.pathSeparator).last;
      final exists = file.existsSync();
      final fileSize = exists ? file.lengthSync() : 0;
      final title = fileName.replaceAll(RegExp(r'\.[^.]+$'), '');

      debugPrint('📥 [SharePayloadProvider] file: $fileName, size: $fileSize, exists: $exists');

      state = SharePayload(
        files: [
          PlatformFile(
            name: fileName,
            path: cleanPath,
            size: fileSize,
          ),
        ],
        defaultTitle: title,
      );
    } catch (e) {
      debugPrint('⚠️ [SharePayloadProvider] Failed to parse file: $e');
    }
  }

  void clear() {
    debugPrint('🧹 [SharePayloadProvider] clear payload');
    state = null;
  }
}

final pendingSharePayloadProvider =
    StateNotifierProvider<SharePayloadNotifier, SharePayload?>(
  (ref) => SharePayloadNotifier(),
);
