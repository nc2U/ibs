import 'dart:async';
import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:receive_sharing_intent/receive_sharing_intent.dart';
import '../providers/share_payload_provider.dart';
import '../router/app_router.dart';
import 'share_action_choice_sheet.dart';

/// 외부 앱(카카오톡, 메일, 시놀로지/구글 드라이브 등)에서
/// [공유] 또는 [다음으로 열기]로 유입된 파일/링크를 감지하여
/// pendingSharePayloadProvider에 등록하고 모달을 띄우는 전역 리스너 위젯
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

    debugPrint('📥 [ShareIntentListener] _handleSharedMedia with ${sharedList.length} items');
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
        var cleanPath = rawPath;
        try {
          cleanPath = Uri.decodeFull(rawPath);
        } catch (_) {
          try {
            cleanPath = Uri.decodeComponent(rawPath);
          } catch (_) {}
        }

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
        } catch (e) {
          debugPrint('⚠️ [ShareIntentListener] Failed to parse shared file: $e');
        }
      }
    }

    if (platformFiles.isNotEmpty || links.isNotEmpty) {
      debugPrint('📥 [ShareIntentListener] Setting payload: ${platformFiles.length} files, ${links.length} links');
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
    // 외부 앱에서 공유된 파일/링크가 등록되었을 때 최상단 네비게이터에 액션 선택 시트 표출
    ref.listen<SharePayload?>(pendingSharePayloadProvider, (prev, next) {
      if (next != null && next.isNotEmpty) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          final navContext = rootNavigatorKey.currentContext;
          if (navContext != null && navContext.mounted) {
            ShareActionChoiceSheet.show(navContext, next);
          }
        });
      }
    });

    // 앱 실행(콜드 스타트) 시 이미 유입되어 대기 중인 공유 파일/링크가 있는 경우 자동 팝업
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final navContext = rootNavigatorKey.currentContext;
      final pending = ref.read(pendingSharePayloadProvider);
      if (pending != null && pending.isNotEmpty && navContext != null && navContext.mounted) {
        ShareActionChoiceSheet.show(navContext, pending);
      }
    });

    return widget.child;
  }
}
