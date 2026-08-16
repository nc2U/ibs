import type { ColumnOption } from '@/views/_Work/components/atomics/ColumnSelector.vue'

// 전체 컬럼 풀 (ColumnSelector용)
export const ALL_PROJECT_COLUMNS: ColumnOption[] = [
  { key: 'name', label: '이름', fixed: true },
  { key: 'slug', label: '식별자' },
  { key: 'description', label: '설명' },
  { key: 'status', label: '상태' },
  { key: 'homepage', label: '홈페이지' },
  { key: 'parent', label: '상위 워크스페이스' },
  { key: 'is_public', label: '공개여부' },
  { key: 'created', label: '등록일' },
  { key: 'updated', label: '수정일' },
]

// 기본 선택 컬럼 키 목록
export const DEFAULT_PROJECT_COLUMNS: string[] = ['name', 'slug', 'description']

// 키-라벨 매핑 객체 (MeetingTable 헤더용)
export const PROJECT_COLUMN_LABEL_MAP: Record<string, string> = Object.fromEntries(
  ALL_PROJECT_COLUMNS.map(col => [col.key, col.label]),
)
