import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_ibs/core/providers/project_provider.dart';
import 'package:mobile_ibs/features/search/data/models/search_model.dart';
import 'package:mobile_ibs/features/search/providers/search_provider.dart';

void main() {
  group('Search Models & Providers Test', () {
    test('UnifiedSearchResponse parses all categories and fields safely', () {
      final json = {
        'issues': [
          {
            'pk': 42,
            'project': {'slug': 'hq-work', 'name': '본사 워크스페이스'},
            'tracker': {'pk': 1, 'name': '기능'},
            'status': {'name': '완료', 'closed': true},
            'subject': '비공개 결재 연동 점검',
            'created': '2026-10-30T09:00:00+09:00',
            'creator': {'pk': 1, 'username': 'koris'},
            'is_private': true,
          }
        ],
        'meetings': [
          {
            'pk': 7,
            'project': {'slug': 'hq-work', 'name': '본사 워크스페이스'},
            'title': '주간 공정 회의',
            'meeting_date': '2026-10-29',
            'status': '2',
            'creator': {'pk': 2, 'username': 'manager'},
          }
        ],
        'documents': [
          {
            'pk': 11,
            'project': {'slug': 'hq-work', 'name': '본사 워크스페이스'},
            'title': '표준 시방서',
            'description': '2026년 개정판',
            'created': '2026-10-20T10:00:00+09:00',
            'creator': null,
          }
        ],
        'news': [
          {
            'pk': 3,
            'project': {'slug': 'hq-work', 'name': '본사 워크스페이스'},
            'title': '시스템 점검 안내',
            'summary': '주말 서버 점검',
            'created': '2026-10-25T10:00:00+09:00',
            'author': {'pk': 1, 'username': 'koris'},
          }
        ],
        'posts': [
          {
            'pk': 99,
            'project': {'slug': 'hq-work', 'name': '본사 워크스페이스'},
            'forum': 5,
            'title': '사내 동호회 모집',
            'created': '2026-10-28T10:00:00+09:00',
            'creator': {'pk': 3, 'username': 'staff'},
          }
        ],
        'comments': [
          {
            'pk': 15,
            'issue': {
              'pk': 42,
              'subject': '비공개 결재 연동 점검',
              'project': {'slug': 'hq-work', 'name': '본사 워크스페이스'},
            },
            'content': '검토 완료했습니다.',
            'created': '2026-10-30T10:00:00+09:00',
            'creator': {'pk': 2, 'username': 'manager'},
          }
        ],
      };

      final response = UnifiedSearchResponse.fromJson(json);

      expect(response.isEmpty, false);
      expect(response.totalCount, 6);

      final issue = response.issues.first;
      expect(issue.pk, 42);
      expect(issue.statusName, '완료');
      expect(issue.statusClosed, true);
      expect(issue.isPrivate, true);
      expect(issue.creator?.username, 'koris');

      final meeting = response.meetings.first;
      expect(meeting.status, '2');
      expect(meeting.statusLabel, '회의 · 종료');

      final comment = response.comments.first;
      expect(comment.issuePk, 42);
      expect(comment.project.slug, 'hq-work');
    });

    test('effectiveSearchScopeProvider falls back to all when project is null', () {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      container.read(searchScopeProvider.notifier).state = 'project';
      expect(container.read(selectedProjectProvider), isNull);
      expect(container.read(effectiveSearchScopeProvider), 'all');

      container.read(selectedProjectProvider.notifier).state = const SelectedProject(
        pk: 1,
        name: '테스트 워크스페이스',
        slug: 'test-ws',
      );
      expect(container.read(effectiveSearchScopeProvider), 'project');

      container.read(searchScopeProvider.notifier).state = 'my';
      expect(container.read(effectiveSearchScopeProvider), 'my');
    });

    test('RecentSearchesNotifier deduplicates, trims, and limits to 10 items', () {
      final notifier = RecentSearchesNotifier(null);

      notifier.addSearch('a'); // 2자 미만 무시
      expect(notifier.state, isEmpty);

      for (int i = 1; i <= 12; i++) {
        notifier.addSearch('검색어 $i');
      }
      expect(notifier.state.length, 10);
      expect(notifier.state.first, '검색어 12');

      // 중복 검색어 입력 시 최상단으로 이동
      notifier.addSearch('  검색어 5  ');
      expect(notifier.state.first, '검색어 5');
      expect(notifier.state.length, 10);

      notifier.removeSearch('검색어 5');
      expect(notifier.state.contains('검색어 5'), false);

      notifier.clearAll();
      expect(notifier.state, isEmpty);
    });
  });
}
