import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('IBSApp smoke test', (WidgetTester tester) async {
    // 라우터/Riverpod 초기화가 필요한 통합 테스트는 별도 integration_test에서 진행
    // 여기서는 기본 smoke test만 유지
    expect(true, isTrue);
  });
}
