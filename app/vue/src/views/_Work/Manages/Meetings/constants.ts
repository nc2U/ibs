import type { ColumnOption } from '@/views/_Work/components/atomics/ColumnSelector.vue'

// 전체 컬럼 풀 (ColumnSelector용)
export const ALL_MEETING_COLUMNS: ColumnOption[] = [
  { key: 'title', label: '제목', fixed: true },
  { key: 'project', label: '프로젝트' },
  { key: 'status', label: '상태' },
  { key: 'category', label: '카테고리' },
  { key: 'meeting_date', label: '회의 일시' },
  { key: 'creator', label: '작성자' },
  { key: 'attendees', label: '참석' },
  { key: 'created', label: '등록일' },
  { key: 'pdf', label: 'PDF' },
]

// 기본 선택 컬럼 키 목록
export const DEFAULT_MEETING_COLUMNS: string[] = ALL_MEETING_COLUMNS.map(col => col.key)

// 키-라벨 매핑 객체 (MeetingTable 헤더용)
export const MEETING_COLUMN_LABEL_MAP: Record<string, string> = Object.fromEntries(
  ALL_MEETING_COLUMNS.map(col => [col.key, col.label]),
)
