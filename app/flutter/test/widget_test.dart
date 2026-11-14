import 'package:flutter_markdown_plus/flutter_markdown_plus.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_widget_from_html/flutter_widget_from_html.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:material_ui/material_ui.dart';
import 'package:mobile_ibs/core/theme/app_theme.dart';
import 'package:mobile_ibs/core/widgets/loading_shimmer.dart';

void main() {
  testWidgets('IBSApp material_ui theme & compatibility bridge smoke test', (
    WidgetTester tester,
  ) async {
    GoogleFonts.config.allowRuntimeFetching = false;

    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('ko', 'KR'),
        supportedLocales: const [Locale('ko', 'KR'), Locale('en', 'US')],
        localizationsDelegates: GlobalMaterialLocalizations.delegates,
        theme: AppTheme.light,
        darkTheme: AppTheme.dark,
        // ignore: deprecated_member_use
        builder: (context, child) => MaterialUiCompatibilityBridge(
          child: child ?? const SizedBox.shrink(),
        ),
        home: const Scaffold(
          body: SingleChildScrollView(
            child: Column(
              children: [
                Text('IBS 웍스'),
                MarkdownBody(data: '**마크다운** 테스트'),
                HtmlWidget('<p>HTML 테스트</p>'),
                LoadingShimmer(itemCount: 1, itemHeight: 64),
              ],
            ),
          ),
        ),
      ),
    );
    await tester.pump();

    expect(find.text('IBS 웍스'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
