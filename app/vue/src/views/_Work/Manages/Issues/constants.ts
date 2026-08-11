import type { ColumnOption } from '@/views/_Work/components/atomics/ColumnSelector.vue'

// 전체 컬럼 풀 (ColumnSelector용)
export const ALL_ISSUE_COLUMNS: ColumnOption[] = [
  { key: 'subject', label: '제목', fixed: true },
  { key: 'project', label: '프로젝트' },
  { key: 'parent', label: '상위업무' },
  { key: 'tracker', label: '유형' },
  { key: 'status', label: '상태' },
  { key: 'priority', label: '우선순위' },
  { key: 'category', label: '범주' },
  { key: 'fixed_version', label: '목표버전' },
  { key: 'assigned_to', label: '담당자' },
  { key: 'watchers', label: '업무관람자' },
  { key: 'is_private', label: '공개여부' },
  { key: 'expected_duration', label: '예상 처리기간' },
  { key: 'start_date', label: '시작일' },
  { key: 'due_date', label: '완료기한' },
  { key: 'done_ratio', label: '진척도' },
  { key: 'meeting', label: '관련 회의' },
  { key: 'sub_issues', label: '하위업무' },
  { key: 'rel_issues', label: '연결된 업무' },
  { key: 'creator', label: '등록자' },
  { key: 'created', label: '등록일' },
  { key: 'updater', label: '최근 수정자' },
  { key: 'updated', label: '변경일' },
]

// 기본 선택 컬럼 키 목록
export const DEFAULT_ISSUE_COLUMNS: string[] = [
  // 'project',
  'tracker',
  'status',
  'priority',
  'fixed_version',
  'subject',
  'assigned_to',
  'updated',
]

// 키-라벨 매핑 객체 (MeetingTable 헤더용)
export const ISSUE_COLUMN_LABEL_MAP: Record<string, string> = Object.fromEntries(
  ALL_ISSUE_COLUMNS.map(col => [col.key, col.label]),
)
