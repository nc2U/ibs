import 'dart:async';
import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:receive_sharing_intent/receive_sharing_intent.dart';
import '../providers/auth_provider.dart';
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
  Timer? _debounceTimer;
  SharePayload? _presentedPayload;

  @override
  void initState() {
    super.initState();
    _initShareIntent();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final pending = ref.read(pendingSharePayloadProvider);
      if (pending != null && pending.isNotEmpty) {
        _scheduleShowSheet(pending);
      }
    });
  }

  void _initShareIntent() {
    if (kIsWeb) return;
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

  /// GoRouter의 초기 리다이렉트 및 라우트 페이지 마운트가 완전히 완료된 후
  /// 안정된 상태에서 안전하게 바텀시트를 호출하는 타이머 가드
  void _scheduleShowSheet(SharePayload? payload) {
    if (payload == null || payload.isEmpty) {
      _debounceTimer?.cancel();
      _presentedPayload = null;
      return;
    }

    if (identical(payload, _presentedPayload) ||
        ShareActionChoiceSheet.isAnyShareSheetOpen) {
      return;
    }

    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 350), () {
      if (!mounted) return;
      if (ShareActionChoiceSheet.isAnyShareSheetOpen) return;

      final currentPayload = ref.read(pendingSharePayloadProvider);
      if (currentPayload == null ||
          currentPayload.isEmpty ||
          identical(currentPayload, _presentedPayload)) {
        return;
      }

      // 인증 검증: 비인가 상태이거나 토큰 로딩 중이면 라우터가 /login으로 가거나 리다이렉트 중이므로 대기
      final isAuth = ref.read(isAuthenticatedProvider);
      if (!isAuth) {
        debugPrint('⏳ [ShareIntentListener] Waiting for authentication before displaying share sheet...');
        return;
      }

      final navContext = rootNavigatorKey.currentContext;
      if (navContext != null && navContext.mounted) {
        _presentedPayload = currentPayload;
        debugPrint('🚀 [ShareIntentListener] Presenting ShareActionChoiceSheet on stable Navigator');
        ShareActionChoiceSheet.show(navContext, currentPayload);
      }
    });
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _intentSub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // 1. 공유 페이로드 변경 감지 시 안정화 후 표출 예약 (null로 초기화되면 재표출 허용 상태 복귀)
    ref.listen<SharePayload?>(pendingSharePayloadProvider, (prev, next) {
      if (next == null || next.isEmpty) {
        _presentedPayload = null;
        _debounceTimer?.cancel();
      } else {
        _scheduleShowSheet(next);
      }
    });

    // 2. 인증 완료 시점 감지 (토큰 비동기 로딩 완료 후 라우트가 /home으로 안착되면 대기 중인 페이로드 표출)
    ref.listen<bool>(isAuthenticatedProvider, (prev, isAuth) {
      if (isAuth) {
        final pending = ref.read(pendingSharePayloadProvider);
        if (pending != null && pending.isNotEmpty) {
          _scheduleShowSheet(pending);
        }
      }
    });

    return widget.child;
  }
}
