import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SharePayload {
  final List<PlatformFile> files;
  final List<String> links;
  final String? defaultTitle;

  const SharePayload({
    this.files = const [],
    this.links = const [];
    this.defaultTitle,
  });

  bool get isEmpty => files.isEmpty && links.isEmpty;
  bool get isNotEmpty => !isEmpty;
}

class SharePayloadNotifier extends StateNotifier<SharePayload?> {
  SharePayloadNotifier() : super(null);

  void setPayload(SharePayload payload) {
    if (payload.isNotEmpty) {
      state = payload;
    }
  }

  void setFromPath(String rawPath) {
    var cleanPath = rawPath;
    if (cleanPath.startsWith('file://')) {
      cleanPath = cleanPath.substring(7);
    }
    cleanPath = Uri.decodeFull(cleanPath);

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
      final fileSize = file.existsSync() ? file.lengthSync() : 0;
      final title = fileName.replaceAll(RegExp(r'\.[^.]+$'), '');

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
    } catch (_) {}
  }

  void clear() {
    state = null;
  }
}

final pendingSharePayloadProvider =
    StateNotifierProvider<SharePayloadNotifier, SharePayload?>(
  (ref) => SharePayloadNotifier(),
);
