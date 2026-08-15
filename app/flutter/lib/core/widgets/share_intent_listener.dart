import 'dart:async';
import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:receive_sharing_intent/receive_sharing_intent.dart';
import '../providers/share_payload_provider.dart';

/// 외부 앱(카카오톡, 메일, 시놀로지/구글 드라이브 등)에서
/// [공유] 또는 [다음으로 열기]로 유입된 파일/링크를 감지하여
/// pendingSharePayloadProvider에 등록하는 전역 리스너 위젯
class ShareIntentListener extends ConsumerStatefulWidget {
  final Widget child;
  const ShareIntentListener({super.key, required this.child});

  @override
  ConsumerState<ShareIntentListener> createState() => _ShareIntentListenerState();
}

class _ShareIntentListenerState extends ConsumerState<ShareIntentListener> {
  StreamSubscription<List<SharedMediaFile>>? _intentSub;

  @override
  void initState() {
    super.initState();
    _initShareIntent();
  }

  void _initShareIntent() {
    // 1. 앱이 실행 중인 상태에서 외부에서 공유된 경우 감지
    _intentSub = ReceiveSharingIntent.instance.getMediaStream().listen((files) {
      if (files.isNotEmpty) {
        _handleSharedMedia(files);
      }
    }, onError: (_) {});

    // 2. 앱이 꺼져있는 상태에서 외부 공유로 앱이 켜진 경우 감지
    ReceiveSharingIntent.instance.getInitialMedia().then((files) {
      if (files.isNotEmpty) {
        _handleSharedMedia(files);
        ReceiveSharingIntent.instance.reset();
      }
    }).catchError((_) {});
  }

  void _handleSharedMedia(List<SharedMediaFile> sharedList) {
    final List<PlatformFile> platformFiles = [];
    final List<String> links = [];
    String? defaultTitle;

    for (final item in sharedList) {
      var rawPath = item.path;

      // 텍스트/URL 공유인 경우
      if (rawPath.startsWith('http://') || rawPath.startsWith('https://')) {
        links.add(rawPath);
        defaultTitle ??= '웹 링크 공유 문서';
      } else {
        // 실제 파일인 경우 (file:// 접두사 및 URI 인코딩 해제)
        if (rawPath.startsWith('file://')) {
          rawPath = rawPath.substring(7);
        }
        final cleanPath = Uri.decodeFull(rawPath);

        try {
          final file = File(cleanPath);
          final fileName = cleanPath.split(Platform.pathSeparator).last;
          final fileSize = file.existsSync() ? file.lengthSync() : 0;

          platformFiles.add(PlatformFile(
            name: fileName,
            path: cleanPath,
            size: fileSize,
          ));

          defaultTitle ??= fileName.replaceAll(RegExp(r'\.[^.]+$'), '');
        } catch (_) {}
      }
    }

    if (platformFiles.isNotEmpty || links.isNotEmpty) {
      ref.read(pendingSharePayloadProvider.notifier).setPayload(
        SharePayload(
          files: platformFiles,
          links: links,
          defaultTitle: defaultTitle,
        ),
      );
    }
  }

  @override
  void dispose() {
    _intentSub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return widget.child;
  }
}
