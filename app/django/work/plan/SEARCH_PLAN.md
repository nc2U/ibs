# Work 앱 통합 검색 기능 구현 계획

> **기준일**: 2026-07-14
> **대상 범위**: `app/django/` (백엔드) + `app/vue/` (프론트엔드)
> **핵심 기술**: PostgreSQL `pg_trgm` GIN 인덱스 + Django APIView

---

## 1. 현황 분석

### 기존 인프라 (재활용 가능)

| 구성요소 | 위치 | 상태 | 비고 |
|----------|------|------|------|
| `Search` 모델 | `work/models/inform.py` | ✅ 존재 | 검색 조건 저장용 골격 완성 |
| `SearchViewSet` | `apiV1/views/work/inform.py` | ✅ 존재 | 현재는 `Search` CRUD만 처리 |
| `issue-search` URL | `apiV1/urls.py:76` | ✅ 등록됨 | `router.register(r'issue-search', work.SearchViewSet)` |
| `IssueFilter` | `apiV1/views/work/issue.py` | ✅ 완성 | `icontains` 기반, 권한 로직 포함 |
| `MeetingFilter.search_filter` | `apiV1/views/work/meeting.py:56` | ✅ 존재 | `title__icontains | content__icontains` |
| `NewsViewSet.get_queryset` | `apiV1/views/work/inform.py:32` | ✅ 완성 | 프로젝트 멤버십 기반 필터 |

### 핵심 문제

`SearchViewSet`이 `Search` 모델의 단순 CRUD만 처리하고,
**실제 멀티모델 검색 실행 로직이 없습니다.**
`IssueViewSet`의 권한 로직(`get_queryset`)도 ViewSet 내부에 결합되어 있어 재사용이 어렵습니다.

---

## 2. 목표 아키텍처

```
GET /api/v1/issue-search/run/?q=비공개&scope=all&t=issues&t=comments&t=meetings&t=news
```

```
┌─────────────────── 프론트엔드 ───────────────────────┐
│  Header 검색창 → /work/search?q=키워드               │
│  Search/Index.vue ──── useSearch (Pinia) ──── API  │
│  SearchResultGroup.vue (타입별 결과 그룹)            │
└──────────────────────────────────────────────────────┘
                         │ HTTP GET
┌─────────────────── 백엔드 ───────────────────────────┐
│  SearchViewSet.run() @action                         │
│      │                                               │
│      ├── build_issue_queryset(user)  ← 핵심 리팩터링 │
│      ├── build_comment_queryset(user)                │
│      ├── build_meeting_queryset(user)                │
│      └── build_news_queryset(user)                   │
│                                                      │
│  각 쿼리: icontains + pg_trgm GIN 인덱스 자동 활용   │
└──────────────────────────────────────────────────────┘
                         │
┌─────────────────── PostgreSQL ───────────────────────┐
│  GIN Index on work_issue(subject, description)       │
│  GIN Index on work_issuecomment(content)             │
│  GIN Index on work_meeting(title, agenda, decisions) │
│  GIN Index on work_news(title, summary, content)     │
└──────────────────────────────────────────────────────┘
```

---

## 3. Phase 1 — DB 인덱스 추가 (pg_trgm)

### 3-1. 마이그레이션

**파일**: `work/migrations/XXXX_add_trgm_search_indexes.py`

```python
from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension


class Migration(migrations.Migration):

    dependencies = [
        ('work', '이전_마이그레이션'),
    ]

    operations = [
        # pg_trgm 확장 활성화 (한 번만 실행됨, superuser 권한 필요)
        TrigramExtension(),

        # Issue: 제목 + 설명
        migrations.RunSQL(
            sql="""
                DROP INDEX IF EXISTS work_issue_subject_like;
                CREATE INDEX work_issue_subject_trgm
                    ON work_issue USING GIN (subject gin_trgm_ops);
                CREATE INDEX work_issue_description_trgm
                    ON work_issue USING GIN (description gin_trgm_ops);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS work_issue_subject_trgm;
                DROP INDEX IF EXISTS work_issue_description_trgm;
            """,
        ),

        # IssueComment: 댓글 내용
        migrations.RunSQL(
            sql="""
                CREATE INDEX work_issuecomment_content_trgm
                    ON work_issuecomment USING GIN (content gin_trgm_ops);
            """,
            reverse_sql="DROP INDEX IF EXISTS work_issuecomment_content_trgm;",
        ),

        # Meeting: 제목 + 의제 + 결정사항
        migrations.RunSQL(
            sql="""
                CREATE INDEX work_meeting_title_trgm
                    ON work_meeting USING GIN (title gin_trgm_ops);
                CREATE INDEX work_meeting_agenda_trgm
                    ON work_meeting USING GIN (agenda gin_trgm_ops);
                CREATE INDEX work_meeting_decisions_trgm
                    ON work_meeting USING GIN (decisions gin_trgm_ops);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS work_meeting_title_trgm;
                DROP INDEX IF EXISTS work_meeting_agenda_trgm;
                DROP INDEX IF EXISTS work_meeting_decisions_trgm;
            """,
        ),

        # News: 제목 + 요약 + 내용
        migrations.RunSQL(
            sql="""
                CREATE INDEX work_news_title_trgm
                    ON work_news USING GIN (title gin_trgm_ops);
                CREATE INDEX work_news_summary_trgm
                    ON work_news USING GIN (summary gin_trgm_ops);
                CREATE INDEX work_news_content_trgm
                    ON work_news USING GIN (content gin_trgm_ops);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS work_news_title_trgm;
                DROP INDEX IF EXISTS work_news_summary_trgm;
                DROP INDEX IF EXISTS work_news_content_trgm;
            """,
        ),
    ]
```

> **주의**: `TrigramExtension()`은 PostgreSQL superuser 권한이 필요합니다.
> Docker 환경에서는 `ibs-postgres` 컨테이너에서 `CREATE EXTENSION pg_trgm;`을 미리 실행하거나,
> `postgres` 슈퍼유저 계정으로 마이그레이션을 실행해야 합니다.

### 3-2. pg_trgm 동작 원리 (코드 변경 없는 이유)

Django의 `__icontains` 룩업은 내부적으로 `ILIKE '%value%'`로 변환됩니다.
`pg_trgm` GIN 인덱스가 존재하면 PostgreSQL 옵티마이저가 **자동으로 인덱스를 선택**합니다.
**애플리케이션 코드 변경이 전혀 필요하지 않습니다.**

---

## 4. Phase 2 — 백엔드 검색 로직

### 4-1. build_issue_queryset() 함수 추출

현재 `IssueViewSet.get_queryset()`의 권한 로직을 모듈 수준 함수로 추출합니다.

**파일**: `apiV1/views/work/issue.py` 상단

```python
def build_issue_queryset(user, base_qs=None):
    """
    사용자 권한에 따른 Issue 쿼리셋을 반환하는 공용 빌더.
    IssueViewSet.get_queryset() 및 검색 View에서 공통 사용.
    """
    if base_qs is None:
        base_qs = Issue.objects.filter(project__status='1').select_related(
            'project', 'status', 'creator', 'assigned_to', 'tracker', 'fixed_version'
        )

    if getattr(user, 'work_manager', False) or user.is_superuser:
        return base_qs

    user_members = Member.objects.filter(user=user).prefetch_related('roles__permissions')
    member_all_pids, member_pub_pids, private_pids = [], [], []
    issue_visibility_order = {'ALL': 3, 'PUB': 2, 'PRI': 1, 'NOP': 0}

    for member in user_members:
        best_visible, has_private_perm = 'NOP', False
        for role in member.roles.all():
            if issue_visibility_order.get(role.issue_visible, 0) > issue_visibility_order.get(best_visible, 0):
                best_visible = role.issue_visible
            for perm in role.permissions.all():
                if perm.code == 'issue.private':
                    has_private_perm = True
        if best_visible == 'ALL':
            member_all_pids.append(member.project_id)
        elif best_visible == 'PUB':
            member_pub_pids.append(member.project_id)
        if has_private_perm:
            private_pids.append(member.project_id)

    from work.models.project import Role
    try:
        non_member_visible = Role.objects.get(pk=2).issue_visible
    except Role.DoesNotExist:
        non_member_visible = 'NOP'

    q_expr = Q(creator=user) | Q(assigned_to=user)
    if member_all_pids:
        q_expr |= Q(project_id__in=member_all_pids)
    if member_pub_pids:
        q_expr |= Q(project_id__in=member_pub_pids, is_private=False)
    if private_pids:
        q_expr |= Q(project_id__in=private_pids)
    if non_member_visible == 'ALL':
        q_expr |= Q(project__is_public=True)
    elif non_member_visible == 'PUB':
        q_expr |= Q(project__is_public=True, is_private=False)

    return base_qs.filter(q_expr).distinct()
```

기존 `IssueViewSet.get_queryset()`은 단순화:

```python
def get_queryset(self):
    return build_issue_queryset(self.request.user, self.queryset)
```

### 4-2. SearchViewSet.run() @action 추가

**파일**: `apiV1/views/work/inform.py`

SearchViewSet에 `@action(detail=False, methods=['get'], url_path='run')` 메서드를 추가하여
통합 검색을 실행합니다. 각 모델별 헬퍼 메서드(`_search_issues`, `_search_comments`,
`_search_meetings`, `_search_news`)를 분리하여 유지보수성을 확보합니다.

파라미터:
- `q` (필수, 2자 이상): 검색어
- `scope`: `'all'` | `'project'` (기본: `'all'`)
- `slug`: 프로젝트 slug (scope='project'일 때 사용)
- `t`: 검색 대상 복수 선택 (기본: `['issues', 'comments', 'meetings', 'news']`)
- `title_only`: `'1'`이면 제목/내용 중 제목만 검색

### 4-3. 검색 전용 Serializer

**신규 파일**: `apiV1/serializers/work/search.py`

각 모델별 경량 Serializer를 정의합니다:
- `IssueSearchSerializer`: pk, project, tracker, status, subject, created, creator, is_private
- `CommentSearchSerializer`: pk, issue(pk+subject+project), content, created, creator
- `MeetingSearchSerializer`: pk, project, title, meeting_date, status, creator
- `NewsSearchSerializer`: pk, project, title, summary, created, author

---

## 5. Phase 3 — 프론트엔드

### 5-1. 파일 구조

```
app/vue/src/
├── store/
│   ├── types/
│   │   └── work_search.ts          # 타입 정의 (신규)
│   └── pinia/
│       └── work_search.ts          # Pinia 스토어 (신규)
└── views/_Work/Manages/
    └── Search/
        ├── Index.vue               # 검색 페이지 진입점 (신규)
        └── components/
            ├── SearchForm.vue      # 검색폼 + 옵션 패널 (신규)
            └── SearchResultGroup.vue  # 타입별 결과 섹션 (신규)
```

### 5-2. 스토어 상태

```
useSearch store
├── query: ref<string>          — 현재 검색어
├── scope: ref<'all'|'project'> — 검색 범위
├── targets: ref<string[]>      — 검색 대상 타입
├── titleOnly: ref<boolean>     — 제목만 검색 여부
├── results: ref<SearchResults> — 검색 결과
├── loading: ref<boolean>
├── error: ref<string|null>
├── totalCount: computed        — 전체 결과 수
├── hasResults: computed
└── fetchSearch(params)         — API 호출
```

### 5-3. URL 라우팅 연동

검색 결과 페이지는 URL 쿼리 파라미터(`?q=키워드`)와 연동합니다.
헤더에서 엔터 → `router.push({ name: 'WorkSearch', query: { q } })` → 
`Index.vue`의 `watch(route.query.q)` → `fetchSearch()` 자동 실행.

이렇게 하면 URL 공유/북마크/뒤로가기가 자연스럽게 동작합니다.

### 5-4. 헤더 검색창

`app/vue/src/views/_Work/components/Header/Index.vue`에
`v-text-field` 검색창을 추가하고 `@keyup.enter` 이벤트로 라우팅합니다.

---

## 6. 구현 체크리스트

### Phase 1 — DB 인덱스

- [ ] Docker `ibs-postgres` 컨테이너에서 `SELECT * FROM pg_extension WHERE extname='pg_trgm';` 확인
- [ ] 없으면 `CREATE EXTENSION pg_trgm;` 실행 (superuser 필요)
- [ ] `work/migrations/XXXX_add_trgm_search_indexes.py` 마이그레이션 파일 생성
- [ ] `sh migrate.sh` 실행 및 인덱스 생성 확인
- [ ] `EXPLAIN ANALYZE SELECT * FROM work_issue WHERE subject ILIKE '%테스트%';`로 인덱스 활용 검증

### Phase 2 — 백엔드

- [ ] `build_issue_queryset(user)` 함수 추출 (`issue.py` 리팩터링)
- [ ] `IssueViewSet.get_queryset()` 단순화
- [ ] `apiV1/serializers/work/search.py` 신규 생성
- [ ] `SearchViewSet.run()` @action 추가 (`inform.py`)
- [ ] `python manage.py check` 오류 없음 확인
- [ ] Docker에서 API 수동 테스트: `GET /api/v1/issue-search/run/?q=테스트`

### Phase 3 — 프론트엔드

- [ ] `store/types/work_search.ts` 타입 정의 생성
- [ ] `store/pinia/work_search.ts` Pinia 스토어 생성
- [ ] `Search/Index.vue` 페이지 컴포넌트 생성
- [ ] `Search/components/SearchForm.vue` 생성
- [ ] `Search/components/SearchResultGroup.vue` 생성
- [ ] 라우터에 `WorkSearch` 등록
- [ ] `Header/Index.vue`에 검색창 통합
- [ ] `pnpm type-check` 오류 없음 확인

---

## 7. API 응답 예시

```json
GET /api/v1/issue-search/run/?q=비공개&t=issues&t=comments

{
  "issues": [
    {
      "pk": 42,
      "project": {"slug": "my-project", "name": "나의 프로젝트"},
      "tracker": {"pk": 1, "name": "기능"},
      "status": {"name": "진행중", "closed": false},
      "subject": "비공개 댓글 처리 로직 구현",
      "created": "2026-07-10T09:00:00+09:00",
      "creator": {"pk": 1, "username": "koris"},
      "is_private": false
    }
  ],
  "comments": [
    {
      "pk": 15,
      "issue": {
        "pk": 42,
        "subject": "비공개 댓글 처리 로직 구현",
        "project": {"slug": "my-project", "name": "나의 프로젝트"}
      },
      "content": "비공개 설정 시 is_blocked 플래그를 사용합니다.",
      "created": "2026-07-11T14:30:00+09:00",
      "creator": {"pk": 2, "username": "team-member"}
    }
  ]
}
```
