import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// 현재 네트워크 연결 상태
enum NetworkStatus { online, offline }

/// connectivity_plus 스트림을 구독하여 온/오프라인 상태를 실시간으로 제공하는 Notifier
class NetworkMonitor extends AsyncNotifier<NetworkStatus> {
  late StreamSubscription<List<ConnectivityResult>> _subscription;

  @override
  Future<NetworkStatus> build() async {
    // 현재 연결 상태 즉시 조회
    final initial = await Connectivity().checkConnectivity();
    state = AsyncData(_resolve(initial));

    // 이후 변경 사항 스트림 구독
    _subscription = Connectivity().onConnectivityChanged.listen((results) {
      state = AsyncData(_resolve(results));
    });

    // Provider가 dispose될 때 구독 해제
    ref.onDispose(() => _subscription.cancel());

    return _resolve(initial);
  }

  NetworkStatus _resolve(List<ConnectivityResult> results) {
    if (results.isEmpty || results.every((r) => r == ConnectivityResult.none)) {
      return NetworkStatus.offline;
    }
    return NetworkStatus.online;
  }
}

/// 전역 네트워크 상태 Provider
final networkMonitorProvider =
    AsyncNotifierProvider<NetworkMonitor, NetworkStatus>(NetworkMonitor.new);

/// 편의용 파생 Provider: 현재 오프라인 여부만 boolean으로 노출
final isOfflineProvider = Provider<bool>((ref) {
  final status = ref.watch(networkMonitorProvider);
  // 아직 초기화 중이거나 오류인 경우에는 온라인으로 간주
  return status.valueOrNull == NetworkStatus.offline;
});
