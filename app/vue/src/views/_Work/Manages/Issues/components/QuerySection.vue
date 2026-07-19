<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, reactive, ref, watch } from 'vue'
import type { selectProject } from '@/store/types/work_project.ts'
import type { IssueFilter, IssueStatus, Tracker } from '@/store/types/work_issue.ts'
import Multiselect from '@vueform/multiselect'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import { useWork } from '@/store/pinia/work_project'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import AllProjectsSelect from '@/views/_Work/components/atomics/AllProjectsSelect.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

const props = defineProps({
  searchProjects: { type: Array as PropType<selectProject[]>, default: () => [] },
  statusList: { type: Array as PropType<IssueStatus[]>, default: () => [] },
  trackerList: { type: Array as PropType<Tracker[]>, default: () => [] },
  priorityList: { type: Array as PropType<any[]>, default: () => [] },
  categoryList: { type: Array as PropType<any[]>, default: () => [] },
  getIssues: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
  getUsers: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
  getVersions: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
})

const { can, PERM } = usePerms()
const workStore = useWork()
const roleList = computed(() => workStore.roleList.filter(r => ![1, 2].includes(r.pk)))

const emit = defineEmits(['filter-submit'])

const viewMode = ref<'board' | 'list'>('board')
const condVisible = ref(true)
const optVisible = ref(false)

const searchCond = ref(['status'])
const resetFilter = () => {
  searchCond.value = ['status']
  filterSubmit()
}

interface OptionItem {
  value: string
  label: string
  disabled?: boolean
}

interface SearchOptionGroup {
  label?: string
  options: OptionItem[]
  disabled?: boolean
}

const searchOptions = reactive<SearchOptionGroup[]>([
  {
    options: [
      { value: 'status', label: '상태', disabled: true },
      { value: 'tracker', label: '유형' },
      { value: 'priority', label: '우선순위' },
      { value: 'author', label: '작성자' },
      { value: 'assignee', label: '담당자' },
      { value: 'version', label: '목표단계' },
      { value: 'category', label: '범주' },
      { value: 'done_ratio', label: '진척도' },
      { value: 'is_private', label: '비공개' },
      { value: 'watcher', label: '업무관람자' },
      { value: 'updater', label: '수정자' },
      { value: 'last_updater', label: '최근수정자' },
      { value: 'issue', label: '업무' },
    ],
  },
  {
    label: '문자열 검색',
    options: [
      { value: 'subject', label: '\u00A0\u00A0\u00A0제목' },
      { value: 'description', label: '\u00A0\u00A0\u00A0설명' },
      { value: 'comment', label: '\u00A0\u00A0\u00A0댓글' },
      { value: 'any_searchable', label: '\u00A0\u00A0\u00A0전체 내용' },
    ],
  },
  {
    label: '날짜별 검색',
    options: [
      { value: 'created', label: '\u00A0\u00A0\u00A0등록일' },
      { value: 'updated', label: '\u00A0\u00A0\u00A0변경일' },
      { value: 'start_date', label: '\u00A0\u00A0\u00A0시작일' },
      { value: 'due_date', label: '\u00A0\u00A0\u00A0완료기한' },
    ],
  },
  {
    label: '파일',
    options: [
      { value: 'file', label: '\u00A0\u00A0\u00A0파일' },
      { value: 'file_desc', label: '\u00A0\u00A0\u00A0파일설명' },
    ],
  },
  {
    label: '역할',
    options: [
      { value: 'creator_role', label: '\u00A0\u00A0\u00A0작성자의 역할' },
      { value: 'assignee_role', label: '\u00A0\u00A0\u00A0담당자의 역할' },
    ],
  },
  {
    label: '목표단계',
    options: [
      { value: 'version_date', label: '\u00A0\u00A0\u00A0목표단계의 날짜' },
      { value: 'version_status', label: '\u00A0\u00A0\u00A0목표단계의 상태' },
    ],
  },
  {
    label: '프로젝트',
    options: [{ value: 'project_status', label: '\u00A0\u00A0\u00A0프로젝트의 상태' }],
  },
  {
    label: '관계',
    options: [
      { value: 'precedes_issue', label: '\u00A0\u00A0\u00A0후속 업무' },
      { value: 'follows_issue', label: '\u00A0\u00A0\u00A0선행 업무' },
      { value: 'parent_issue', label: '\u00A0\u00A0\u00A0상위 업무' },
      { value: 'sub_issue', label: '\u00A0\u00A0\u00A0하위 업무' },
    ],
  },
])

const cond = ref<Record<string, any>>({
  status: 'open' as 'open' | 'is' | 'exclude' | 'closed' | 'any',
  project: 'is' as 'is' | 'exclude',
  tracker: 'is' as 'is' | 'exclude',
  priority: 'is' as 'is' | 'exclude',
  author: 'is' as 'is' | 'exclude',
  assignee: 'is' as 'is' | 'exclude' | 'none' | 'any',
  version: 'is' as 'is' | 'exclude' | 'none' | 'any',
  category: 'is' as 'is' | 'exclude' | 'none' | 'any',
  done_ratio: 'is' as 'is' | 'gte' | 'lte' | 'between' | 'none' | 'any',
  is_private: 'is' as 'is' | 'exclude',
  watcher: 'is' as 'is' | 'exclude',
  updater: 'is' as 'is' | 'exclude',
  last_updater: 'is' as 'is' | 'exclude',
  version_status: 'is' as 'is' | 'exclude',
  project_status: 'is' as 'is' | 'exclude',
  sub_project: 'any' as 'any' | 'none' | 'is' | 'exclude',
  issue: 'is' as 'is' | 'gte' | 'lte' | 'between',
  subject: 'contains' as 'contains' | 'exclude',
  description: 'contains' as 'contains' | 'exclude',
  comment: 'contains' as 'contains' | 'exclude',
  any_searchable: 'contains' as 'contains' | 'exclude',
  created: 'is' as 'is' | 'gte' | 'lte' | 'between' | 'none' | 'any',
  updated: 'is' as 'is' | 'gte' | 'lte' | 'between' | 'none' | 'any',
  start_date: 'is' as 'is' | 'gte' | 'lte' | 'between' | 'none' | 'any',
  due_date: 'is' as 'is' | 'gte' | 'lte' | 'between' | 'none' | 'any',
  file: 'contains' as 'contains' | 'exclude',
  file_desc: 'contains' as 'contains' | 'exclude',
  creator_role: 'is' as 'is' | 'exclude',
  assignee_role: 'is' as 'is' | 'exclude',
  version_date: 'is' as 'is' | 'lte' | 'gte' | 'between' | 'none' | 'any',
  follows_issue: 'is' as 'is' | 'exclude' | 'none' | 'any',
  precedes_issue: 'is' as 'is' | 'exclude' | 'none' | 'any',
  parent_issue: 'is' as 'is' | 'exclude' | 'contains' | 'none' | 'any',
  parent: 'is' as 'is' | 'exclude' | 'contains' | 'none' | 'any',
})

const route = useRoute()
const form = ref<IssueFilter & Record<string, any>>({
  status__closed: '',
  status: null,
  status__exclude: null,
  project: (route.params.projId as string) ?? '',
  project__search: '',
  project__exclude: '',
  tracker: null,
  tracker__exclude: null,
  priority: null,
  priority__exclude: null,
  category: null,
  category__exclude: null,
  category__isnull: '0',
  is_private: null as boolean | null,
  watcher: null,
  watcher__exclude: null,
  done_ratio: null,
  done_ratio__gte: null,
  done_ratio__lte: null,
  done_ratio__between: '',
  done_ratio__between_min: null,
  done_ratio__between_max: null,
  done_ratio__isnull: '0',
  author: null,
  author__exclude: null,
  updater: null,
  updater__exclude: null,
  last_updater: null,
  last_updater__exclude: null,
  assignee: null,
  assignee__exclude: null,
  version: null,
  version__exclude: null,
  version__isnull: '0',
  id: null,
  id__gte: null,
  id__lte: null,
  id__between: '',
  id__between_min: null,
  id__between_max: null,
  id__any: '',
  subject: '',
  subject__exclude: '',
  description: '',
  description__exclude: '',
  comment: '',
  comment__exclude: '',
  any_searchable: '',
  any_searchable__exclude: '',
  file: '',
  file__exclude: '',
  file_desc: '',
  file_desc__exclude: '',
  parent_issue: null, // 상위업무
  parent_issue__exclude: null,
  parent_issue__contains: '',
  parent_issue__isnull: '0',
  parent: null, // 하위업무
  parent__exclude: null,
  parent__contains: '',
  parent__isnull: '0',
  follows_issue: null, // 선행업무
  follows_issue__exclude: null,
  follows_issue__isnull: '0',
  precedes_issue: null, // 후속업무
  precedes_issue__exclude: null,
  precedes_issue__isnull: '0',
  project__my_project: undefined,
  created: '',
  created__gte: '',
  created__lte: '',
  created__between_min: '',
  created__between_max: '',
  updated: '',
  updated__gte: '',
  updated__lte: '',
  updated__between_min: '',
  updated__between_max: '',
  start_date: '',
  start_date__gte: '',
  start_date__lte: '',
  start_date__between_min: '',
  start_date__between_max: '',
  due_date: '',
  due_date__gte: '',
  due_date__lte: '',
  due_date__between_min: '',
  due_date__between_max: '',
  due_date__isnull: '0',
  creator_role: null,
  creator_role__exclude: null,
  assignee_role: null,
  assignee_role__exclude: null,
  version_date: '',
  version_date__gte: '',
  version_date__lte: '',
  version_date__between_min: '',
  version_date__between_max: '',
  version_date__isnull: '0',
  version_status: '',
  version_status__exclude: '',
  project_status: '',
  project_status__exclude: '',
  sub_project: null,
  sub_project__exclude: null,
  sub_project__isnull: '0',
})

const subProjects = computed(() => workStore.currentProject?.sub_projects || [])
const hasSubProjects = computed(() => subProjects.value.length > 0)

// Dynamic Form field rendering configuration
const filterFieldsConfig = computed(() => {
  return [
    {
      key: 'project',
      label: '프로젝트',
      type: 'project',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
    },
    {
      key: 'tracker',
      label: '유형',
      type: 'select',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
      options: props.trackerList.map(t => ({ value: t.pk, label: t.name })),
    },
    {
      key: 'priority',
      label: '우선순위',
      type: 'select',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
      options: props.priorityList.map(p => ({ value: p.pk, label: p.name })),
    },
    {
      key: 'author',
      label: '작성자',
      type: 'multiselect',
      placeholder: '작성자',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
      options: props.getUsers,
    },
    {
      key: 'assignee',
      label: '담당자',
      type: 'multiselect',
      placeholder: '담당자',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
        { value: 'none', label: '없음' },
        { value: 'any', label: '모두' },
      ],
      options: props.getUsers,
    },
    {
      key: 'version',
      label: '목표단계',
      type: 'multiselect',
      placeholder: '목표단계',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
        { value: 'none', label: '없음' },
        { value: 'any', label: '모두' },
      ],
      options: props.getVersions,
    },
    {
      key: 'category',
      label: '범주',
      type: 'select',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
        { value: 'none', label: '없음' },
        { value: 'any', label: '모두' },
      ],
      options: props.categoryList.map(c => ({ value: c.pk, label: c.name })),
    },
    {
      key: 'done_ratio',
      label: '진척도',
      type: 'range',
      placeholder: '진척도 (%)',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'gte', label: '>=' },
        { value: 'lte', label: '<=' },
        { value: 'between', label: '사이' },
        { value: 'none', label: '없음' },
        { value: 'any', label: '모두' },
      ],
    },
    {
      key: 'is_private',
      label: '비공개',
      type: 'none',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
    },
    {
      key: 'watcher',
      label: '업무관람자',
      type: 'multiselect',
      placeholder: '업무관람자',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
      options: props.getUsers,
    },
    {
      key: 'updater',
      label: '수정자',
      type: 'multiselect',
      placeholder: '수정자',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
      options: props.getUsers,
    },
    {
      key: 'last_updater',
      label: '최근수정자',
      type: 'multiselect',
      placeholder: '최근수정자',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
      options: props.getUsers,
    },
    {
      key: 'sub_project',
      label: '하위 프로젝트',
      type: 'sub_project',
      condOptions: [
        { value: 'any', label: '모두' },
        { value: 'none', label: '없음' },
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
    },
    {
      key: 'project_status',
      label: '프로젝트의 상태',
      type: 'select',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
      options: [
        { value: '1', label: '사용중' },
        { value: '2', label: '닫힘' },
      ],
    },
    {
      key: 'issue',
      label: '업무',
      type: 'range',
      placeholder: 'ID',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'gte', label: '>=' },
        { value: 'lte', label: '<=' },
        { value: 'between', label: '사이' },
      ],
    },
    {
      key: 'subject',
      label: '제목',
      type: 'text-match',
      placeholder: '제목 키워드',
      condOptions: [
        { value: 'contains', label: '포함되는 키워드' },
        { value: 'exclude', label: '포함하지 않는 키워드' },
      ],
    },
    {
      key: 'description',
      label: '설명',
      type: 'text-match',
      placeholder: '설명 키워드',
      condOptions: [
        { value: 'contains', label: '포함되는 키워드' },
        { value: 'exclude', label: '포함하지 않는 키워드' },
      ],
    },
    {
      key: 'comment',
      label: '댓글',
      type: 'text-match',
      placeholder: '댓글 키워드',
      condOptions: [
        { value: 'contains', label: '포함되는 키워드' },
        { value: 'exclude', label: '포함하지 않는 키워드' },
      ],
    },
    {
      key: 'any_searchable',
      label: '전체 내용',
      type: 'text-match',
      placeholder: '검색 키워드 (제목, 설명, 댓글)',
      condOptions: [
        { value: 'contains', label: '포함되는 키워드' },
        { value: 'exclude', label: '포함하지 않는 키워드' },
      ],
    },
    {
      key: 'created',
      label: '등록일',
      type: 'date',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'lte', label: '이전' },
        { value: 'gte', label: '이후' },
        { value: 'between', label: '사이' },
      ],
    },
    {
      key: 'updated',
      label: '변경일',
      type: 'date',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'lte', label: '이전' },
        { value: 'gte', label: '이후' },
        { value: 'between', label: '사이' },
      ],
    },
    {
      key: 'start_date',
      label: '시작일',
      type: 'date',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'lte', label: '이전' },
        { value: 'gte', label: '이후' },
        { value: 'between', label: '사이' },
      ],
    },
    {
      key: 'due_date',
      label: '완료기한',
      type: 'date',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'lte', label: '이전' },
        { value: 'gte', label: '이후' },
        { value: 'between', label: '사이' },
        { value: 'none', label: '없음' },
        { value: 'any', label: '모두' },
      ],
    },
    {
      key: 'file',
      label: '파일',
      type: 'text-match',
      placeholder: '파일명 키워드',
      condOptions: [
        { value: 'contains', label: '포함되는 키워드' },
        { value: 'exclude', label: '포함하지 않는 키워드' },
      ],
    },
    {
      key: 'file_desc',
      label: '파일설명',
      type: 'text-match',
      placeholder: '파일설명 키워드',
      condOptions: [
        { value: 'contains', label: '포함되는 키워드' },
        { value: 'exclude', label: '포함하지 않는 키워드' },
      ],
    },
    {
      key: 'creator_role',
      label: '작성자의 역할',
      type: 'role',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
    },
    {
      key: 'assignee_role',
      label: '담당자의 역할',
      type: 'role',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
    },
    {
      key: 'version_date',
      label: '목표단계의 날짜',
      type: 'date',
      placeholder: '목표단계 완료 기한',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'lte', label: '이내' },
        { value: 'gte', label: '이후' },
        { value: 'between', label: '사이' },
        { value: 'none', label: '없음' },
        { value: 'any', label: '모두' },
      ],
    },
    {
      key: 'version_status',
      label: '목표단계의 상태',
      type: 'select',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
      options: [
        { value: '1', label: '진행' },
        { value: '2', label: '잠김' },
        { value: '3', label: '닫힘' },
      ],
    },
    {
      key: 'follows_issue',
      label: '선행업무',
      type: 'number',
      placeholder: '선행업무 ID 입력',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
        { value: 'none', label: '없음' },
        { value: 'any', label: '모두' },
      ],
    },
    {
      key: 'precedes_issue',
      label: '후속업무',
      type: 'number',
      placeholder: '후속업무 ID 입력',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
        { value: 'none', label: '없음' },
        { value: 'any', label: '모두' },
      ],
    },
    {
      key: 'parent_issue',
      label: '상위업무',
      type: 'relation',
      placeholder: '상위업무 ID 입력',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
        { value: 'contains', label: '포함되는 키워드' },
        { value: 'none', label: '없음' },
        { value: 'any', label: '모두' },
      ],
    },
    {
      key: 'sub_issue',
      label: '하위업무',
      type: 'relation',
      placeholder: '하위업무 ID 입력',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
        { value: 'contains', label: '포함되는 키워드' },
        { value: 'none', label: '없음' },
        { value: 'any', label: '모두' },
      ],
    },
  ]
})

const activeFields = computed(() => {
  return filterFieldsConfig.value.filter(
    field =>
      searchCond.value.includes(field.key) && (field.key !== 'sub_project' || hasSubProjects.value),
  )
})

const filterSubmit = () => {
  const filterData = {
    status__closed: '0',
    project_status: '1',
  } as IssueFilter & Record<string, any>

  // 기본 프로젝트 조회 (project__slug) 세팅
  if (form.value.project) {
    filterData.project__slug = form.value.project
  }

  // 1. 상태 필터링 처리
  if (cond.value.status === 'open') {
    filterData.status__closed = '0'
    filterData.status = null
    filterData.status__exclude = null
  } else if (cond.value.status === 'is') {
    filterData.status = form.value.status
    filterData.status__closed = ''
    filterData.status__exclude = null
  } else if (cond.value.status === 'exclude') {
    filterData.status__exclude = form.value.status
    filterData.status = null
    filterData.status__closed = ''
  } else if (cond.value.status === 'closed') {
    filterData.status__closed = '1'
    filterData.status = null
    filterData.status__exclude = null
  } else if (cond.value.status === 'any') {
    filterData.status__closed = ''
    filterData.status = null
    filterData.status__exclude = null
  }

  // 2. 검색 활성화 필드들에 대해 일반 규칙에 의거하여 dynamic payload 빌드
  searchCond.value.forEach(key => {
    // status는 특수 처리했으므로 제외
    if (key === 'status') return

    // sub_issue는 form/cond 내부 키가 parent임
    const fieldKey = key === 'sub_issue' ? 'parent' : key
    const operator = cond.value[fieldKey]
    const val = form.value[fieldKey]

    // 단순 필드 및 예외/isnull 공통 매핑
    if (operator === 'is') {
      if (key === 'project') {
        if (form.value.project === '') {
          filterData.project__my_project = true
          delete filterData.project__slug
        } else {
          filterData.project__search = form.value.project
        }
      } else if (key === 'is_private') {
        filterData.is_private = true
      } else {
        filterData[fieldKey] = val
      }
    } else if (operator === 'exclude') {
      if (key === 'project') {
        if (form.value.project === '') {
          filterData.project__my_project = false
          delete filterData.project__slug
        } else {
          filterData.project__exclude = form.value.project
          delete filterData.project__slug
        }
      } else if (key === 'is_private') {
        filterData.is_private = false
      } else {
        filterData[`${fieldKey}__exclude`] = val
      }
    } else if (operator === 'none') {
      filterData[`${fieldKey}__isnull`] = '1'
    } else if (operator === 'any') {
      filterData[`${fieldKey}__isnull`] = '0'
    } else if (operator === 'contains') {
      filterData[fieldKey] = val
    } else if (operator === 'gte') {
      if (key === 'issue') filterData.id__gte = form.value.id__gte
      else filterData[`${fieldKey}__gte`] = form.value[`${fieldKey}__gte`]
    } else if (operator === 'lte') {
      if (key === 'issue') filterData.id__lte = form.value.id__lte
      else filterData[`${fieldKey}__lte`] = form.value[`${fieldKey}__lte`]
    } else if (operator === 'between') {
      let min = ''
      let max = ''
      if (key === 'issue') {
        min = form.value.id__between_min !== null ? String(form.value.id__between_min) : ''
        max = form.value.id__between_max !== null ? String(form.value.id__between_max) : ''
        if (min || max) filterData.id__between = `${min},${max}`
      } else {
        min = form.value[`${fieldKey}__between_min`] || ''
        max = form.value[`${fieldKey}__between_max`] || ''
        if (min || max) filterData[`${fieldKey}__between`] = `${min},${max}`
      }
    }
  })

  // my project 강제 덮어쓰기가 있을 경우
  if (form.value.project__my_project !== undefined) {
    filterData.project__my_project = form.value.project__my_project
  }

  console.log(filterData)
  emit('filter-submit', filterData)
}

// 4개의 리스트에 대해 watchEffect로 통합 감시하여 초기 설정 처리
const listStateToWatch = computed(() => ({
  status: props.statusList,
  tracker: props.trackerList,
  priority: props.priorityList,
  category: props.categoryList,
}))

watch(
  listStateToWatch,
  lists => {
    if (lists.status.length && !form.value.status) form.value.status = lists.status[0]?.pk
    if (lists.tracker.length && !form.value.tracker) form.value.tracker = lists.tracker[0]?.pk
    if (lists.priority.length && !form.value.priority) form.value.priority = lists.priority[0]?.pk
    if (lists.category.length && !form.value.category) form.value.category = lists.category[0]?.pk
  },
  { immediate: true },
)

watch(searchCond, nVal => {
  if (nVal.includes('project')) form.value.project = ''
  if (nVal.includes('tracker') && !form.value.tracker) form.value.tracker = props.trackerList[0]?.pk
  if (nVal.includes('priority') && !form.value.priority)
    form.value.priority = props.priorityList[0]?.pk
  if (nVal.includes('category') && !form.value.category)
    form.value.category = props.categoryList[0]?.pk
  if (nVal.includes('watcher') && !form.value.watcher) form.value.watcher = props.getUsers[0]?.value
  if (nVal.includes('updater') && !form.value.updater) form.value.updater = props.getUsers[0]?.value
  if (nVal.includes('last_updater') && !form.value.last_updater)
    form.value.last_updater = props.getUsers[0]?.value
  if (!nVal.includes('status')) searchCond.value = ['status']
})

watch(
  hasSubProjects,
  hasSubs => {
    const subIdx = searchOptions[0].options.findIndex(o => o.value === 'sub_project')
    if (hasSubs) {
      if (subIdx === -1) {
        const issueIdx = searchOptions[0].options.findIndex(o => o.value === 'issue')
        if (issueIdx > -1) {
          searchOptions[0].options.splice(issueIdx, 0, {
            value: 'sub_project',
            label: '하위 프로젝트',
          })
        } else {
          searchOptions[0].options.push({ value: 'sub_project', label: '하위 프로젝트' })
        }
      }
    } else {
      if (subIdx > -1) {
        searchOptions[0].options.splice(subIdx, 1)
        const activeIdx = searchCond.value.indexOf('sub_project')
        if (activeIdx > -1) {
          searchCond.value.splice(activeIdx, 1)
        }
      }
    }
  },
  { immediate: true },
)

onBeforeMount(async () => {
  if (!!props.statusList.length) form.value.status = props.statusList[0]?.pk

  // 프로젝트 환경인지 체크하여 범주(category) 옵션 제어
  if (route.params.projId) {
    const categoryOpt = searchOptions[0].options.find(o => o.value === 'category')
    if (categoryOpt) delete categoryOpt.disabled
  } else {
    const categoryIdx = searchOptions[0].options.findIndex(o => o.value === 'category')
    if (categoryIdx > -1) searchOptions[0].options.splice(categoryIdx, 1)
  }

  // 비공개 업무 권한 검사 (issue.private 권한)
  const canPrivate = can(PERM.ISSUE_PRIVATE)
  if (canPrivate) {
    const privateOpt = searchOptions[0].options.find(o => o.value === 'is_private')
    if (privateOpt) delete privateOpt.disabled
  } else {
    const privateIdx = searchOptions[0].options.findIndex(o => o.value === 'is_private')
    if (privateIdx > -1) searchOptions[0].options.splice(privateIdx, 1)
  }

  if (route.name === '업무')
    searchOptions[0].options.splice(1, 0, { value: 'project', label: '프로젝트' })

  if (!!route.query.status)
    cond.value.status = route.query.status as 'open' | 'is' | 'exclude' | 'closed' | 'any'
  if (!!route.query.tracker) {
    searchCond.value.push('tracker')
    form.value.tracker = Number(route.query.tracker)
    cond.value.tracker = 'is'
  }
  if (!!route.query.author) {
    searchCond.value.push('author')
    form.value.author = Number(route.query.author)
  }
  if (!!route.query.assignee) {
    searchCond.value.push('assignee')
    form.value.assignee = Number(route.query.assignee)
  }
  if (!!route.query.version) {
    searchCond.value.push('version')
    form.value.version = Number(route.query.version)
  }
  if (!!route.query.parent) {
    searchCond.value.push('parent')
    form.value.parent = Number(route.query.parent)
  }
  setTimeout(() => filterSubmit(), 50)
})
</script>

<template>
  <CRow>
    <CCol class="pointer pt-1 mb-0" @click="condVisible = !condVisible">
      <v-icon :icon="condVisible ? 'mdi-chevron-down' : 'mdi-chevron-right'" size="sm" />
      검색조건
    </CCol>
    <v-divider class="mx-3 mt-2 mb-0" />

    <CCollapse :visible="condVisible">
      <slot name="condition">
        <CRow class="m-2" color="light">
          <CCol class="col-12 col-md-8">
            <!-- 1. 고정 필터: 상태 (Status) -->
            <CRow>
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck label="상태" id="status" checked="true" readonly />
              </CCol>
              <CCol class="d-none d-lg-block col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.status" size="sm">
                  <option value="open">진행중</option>
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                  <option value="closed">완료됨</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <CFormSelect
                  v-if="cond.status === 'is' || cond.status === 'exclude'"
                  v-model="form.status"
                  size="sm"
                >
                  <option v-for="status in statusList" :value="status.pk" :key="status.pk">
                    {{ status.name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>

            <!-- 2. 동적 추가 필터 리스트 루프 렌더링 -->
            <template v-for="field in activeFields" :key="field.key">
              <CRow>
                <!-- 라벨 & 체크박스 (Readonly) -->
                <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                  <CFormCheck checked readonly :label="field.label" :id="field.key" />
                </CCol>

                <!-- 연산자 조건 선택기 (is, exclude, gte, lte, between 등) -->
                <CCol class="col-4 col-lg-3 col-xl-2">
                  <CFormSelect
                    v-model="cond[field.key === 'sub_issue' ? 'parent' : field.key]"
                    size="sm"
                  >
                    <option v-for="opt in field.condOptions" :key="opt.value" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </CFormSelect>
                </CCol>

                <!-- 실제 입력 필드 렌더링부 -->
                <CCol class="col-4 col-lg-3">
                  <!-- 프로젝트 전용 셀렉트 -->
                  <template v-if="field.type === 'project'">
                    <AllProjectsSelect
                      v-model="form.project"
                      :search-projects="searchProjects"
                      default-title="<< 내 프로젝트 >>"
                      value-type="slug"
                      size="sm"
                    />
                  </template>

                  <!-- 일반 셀렉트 -->
                  <template v-else-if="field.type === 'select'">
                    <CFormSelect
                      v-if="cond[field.key] === 'is' || cond[field.key] === 'exclude'"
                      v-model="form[field.key]"
                      size="sm"
                      @change="filterSubmit"
                    >
                      <option v-for="opt in field.options" :key="opt.value" :value="opt.value">
                        {{ opt.label }}
                      </option>
                    </CFormSelect>
                  </template>

                  <!-- 역할 셀렉트 -->
                  <template v-else-if="field.type === 'role'">
                    <CFormSelect
                      v-if="cond[field.key] === 'is'"
                      v-model="form[field.key]"
                      size="sm"
                      @change="filterSubmit"
                    >
                      <option v-for="r in roleList" :key="r.pk" :value="r.pk">
                        {{ r.name }}
                      </option>
                    </CFormSelect>
                    <CFormSelect
                      v-if="cond[field.key] === 'exclude'"
                      v-model="form[`${field.key}__exclude`]"
                      size="sm"
                      @change="filterSubmit"
                    >
                      <option v-for="r in roleList" :key="r.pk" :value="r.pk">
                        {{ r.name }}
                      </option>
                    </CFormSelect>
                  </template>

                  <!-- 하위 프로젝트 셀렉트 -->
                  <template v-else-if="field.type === 'sub_project'">
                    <CFormSelect
                      v-if="cond.sub_project === 'is'"
                      v-model="form.sub_project"
                      size="sm"
                      @change="filterSubmit"
                    >
                      <option :value="null">하위 프로젝트 선택</option>
                      <option v-for="p in subProjects" :key="p.pk" :value="p.pk">
                        {{ p.name }}
                      </option>
                    </CFormSelect>
                    <CFormSelect
                      v-if="cond.sub_project === 'exclude'"
                      v-model="form.sub_project__exclude"
                      size="sm"
                      @change="filterSubmit"
                    >
                      <option :value="null">하위 프로젝트 선택</option>
                      <option v-for="p in subProjects" :key="p.pk" :value="p.pk">
                        {{ p.name }}
                      </option>
                    </CFormSelect>
                  </template>

                  <!-- 멀티 셀렉트 (Multiselect) -->
                  <template v-else-if="field.type === 'multiselect'">
                    <Multiselect
                      v-if="cond[field.key] === 'is' || cond[field.key] === 'exclude'"
                      v-model="form[field.key]"
                      :options="field.options"
                      :placeholder="field.placeholder"
                      searchable
                      @keydown.enter="filterSubmit"
                    />
                  </template>

                  <!-- 텍스트 매칭 검색 필드 -->
                  <template v-else-if="field.type === 'text-match'">
                    <CFormInput
                      v-if="cond[field.key] === 'contains'"
                      v-model="form[field.key]"
                      :placeholder="field.placeholder"
                      style="height: 30px"
                      @keydown.enter="filterSubmit"
                    />
                    <CFormInput
                      v-if="cond[field.key] === 'exclude'"
                      v-model="form[`${field.key}__exclude`]"
                      :placeholder="'제외할 ' + field.placeholder"
                      style="height: 30px"
                      @keydown.enter="filterSubmit"
                    />
                  </template>

                  <!-- 수치 범위 검색 필드 (done_ratio, issue 등) -->
                  <template v-else-if="field.type === 'range'">
                    <CFormInput
                      v-if="cond[field.key] === 'is'"
                      v-model="form[field.key === 'issue' ? 'id' : field.key]"
                      placeholder="ID"
                      style="height: 30px"
                      @keydown.enter="filterSubmit"
                    />
                    <CFormInput
                      v-if="cond[field.key] === 'gte'"
                      v-model="form[field.key === 'issue' ? 'id__gte' : `${field.key}__gte`]"
                      :placeholder="field.key === 'done_ratio' ? '이상 (%)' : '이상'"
                      style="height: 30px"
                      @keydown.enter="filterSubmit"
                    />
                    <CFormInput
                      v-if="cond[field.key] === 'lte'"
                      v-model="form[field.key === 'issue' ? 'id__lte' : `${field.key}__lte`]"
                      :placeholder="field.key === 'done_ratio' ? '이하 (%)' : '이하'"
                      style="height: 30px"
                      @keydown.enter="filterSubmit"
                    />
                    <CFormInput
                      v-if="cond[field.key] === 'between'"
                      v-model="
                        form[
                          field.key === 'issue' ? 'id__between_min' : `${field.key}__between_min`
                        ]
                      "
                      type="number"
                      :placeholder="field.key === 'done_ratio' ? '최소 (%)' : '최소 ID'"
                      style="height: 30px"
                      @keydown.enter="filterSubmit"
                    />
                  </template>

                  <!-- 날짜 입력 필드 (DatePicker) -->
                  <template v-else-if="field.type === 'date'">
                    <DatePicker
                      v-if="cond[field.key] === 'is'"
                      v-model="form[field.key]"
                      :placeholder="field.placeholder || field.label"
                      @update:model-value="filterSubmit"
                    />
                    <DatePicker
                      v-if="cond[field.key] === 'lte'"
                      v-model="form[`${field.key}__lte`]"
                      placeholder="이전"
                      @update:model-value="filterSubmit"
                    />
                    <DatePicker
                      v-if="cond[field.key] === 'gte'"
                      v-model="form[`${field.key}__gte`]"
                      placeholder="이후"
                      @update:model-value="filterSubmit"
                    />
                    <div v-if="cond[field.key] === 'between'" class="d-flex align-items-center">
                      <DatePicker
                        v-model="form[`${field.key}__between_min`]"
                        placeholder="시작일"
                        @update:model-value="filterSubmit"
                      />
                      <span class="mx-2">~</span>
                      <DatePicker
                        v-model="form[`${field.key}__between_max`]"
                        placeholder="종료일"
                        @update:model-value="filterSubmit"
                      />
                    </div>
                  </template>

                  <!-- 단순 수치형 입력 필드 -->
                  <template v-else-if="field.type === 'number'">
                    <CFormInput
                      v-if="cond[field.key] === 'is'"
                      v-model.number="form[field.key]"
                      type="number"
                      :placeholder="field.placeholder"
                      size="sm"
                      @keydown.enter="filterSubmit"
                    />
                    <CFormInput
                      v-if="cond[field.key] === 'exclude'"
                      v-model.number="form[`${field.key}__exclude`]"
                      type="number"
                      :placeholder="field.placeholder"
                      size="sm"
                      @keydown.enter="filterSubmit"
                    />
                  </template>

                  <!-- 관계 업무 입력 필드 (상위업무, 하위업무) -->
                  <template v-else-if="field.type === 'relation'">
                    <CFormInput
                      v-if="cond[field.key === 'sub_issue' ? 'parent' : field.key] === 'is'"
                      v-model.number="form[field.key === 'sub_issue' ? 'parent' : field.key]"
                      type="number"
                      :placeholder="field.label + ' ID 입력'"
                      size="sm"
                      @keydown.enter="filterSubmit"
                    />
                    <CFormInput
                      v-if="cond[field.key === 'sub_issue' ? 'parent' : field.key] === 'exclude'"
                      v-model.number="
                        form[
                          field.key === 'sub_issue' ? 'parent__exclude' : `${field.key}__exclude`
                        ]
                      "
                      type="number"
                      :placeholder="field.label + ' ID 입력'"
                      size="sm"
                      @keydown.enter="filterSubmit"
                    />
                    <CFormInput
                      v-if="cond[field.key === 'sub_issue' ? 'parent' : field.key] === 'contains'"
                      v-model="
                        form[
                          field.key === 'sub_issue' ? 'parent__contains' : `${field.key}__contains`
                        ]
                      "
                      placeholder="제목 키워드 입력"
                      size="sm"
                      @keydown.enter="filterSubmit"
                    />
                  </template>
                </CCol>

                <!-- 범위형에서 '사이(between)' 조건일 때 출력할 최대값 입력창 -->
                <CCol
                  v-if="field.type === 'range' && cond[field.key] === 'between'"
                  class="col-4 col-lg-3"
                >
                  <CFormInput
                    v-model="
                      form[field.key === 'issue' ? 'id__between_max' : `${field.key}__between_max`]
                    "
                    type="number"
                    :placeholder="field.key === 'done_ratio' ? '최대 (%)' : '최대 ID'"
                    style="height: 30px"
                    @keydown.enter="filterSubmit"
                  />
                </CCol>
              </CRow>
            </template>
          </CCol>

          <CCol md="4" class="text-right">
            <CRow>
              <CFormLabel
                for="searchOptions"
                class="col-4 col-lg-2 col-xl-4 col-xxl-5 col-form-label d-block d-md-none d-lg-block"
              >
                검색조건 추가
              </CFormLabel>
              <CCol class="col-8 col-md-12 col-lg-10 col-xl-8 col-xxl-7">
                <Multiselect
                  mode="tags"
                  v-model="searchCond"
                  id="searchOptions"
                  :groups="true"
                  :options="searchOptions"
                  class="multiselect-blue"
                  placeholder="검색조건 추가"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>
      </slot>
    </CCollapse>
  </CRow>

  <CRow class="mt-2">
    <CCol class="pointer mb-0" @click="optVisible = !optVisible">
      <v-icon :icon="optVisible ? 'mdi-chevron-down' : 'mdi-chevron-right'" size="sm" />
      옵션
    </CCol>
    <v-divider class="mx-3 mt-2 mb-0" />
    <CCollapse :visible="optVisible">
      <slot name="option">
        <CRow class="m-2" color="light">
          <CCol>
            <span class="mr-3">결과 표시 </span>
            <CFormCheck
              v-model="viewMode"
              label="보드"
              name="viewMode"
              value="board"
              inline
              type="radio"
            />
            <CFormCheck
              v-model="viewMode"
              label="목록"
              name="viewMode"
              value="list"
              inline
              type="radio"
              disabled
            />
          </CCol>
        </CRow>
      </slot>
    </CCollapse>
  </CRow>

  <CRow class="my-3">
    <CCol>
      <slot name="footer">
        <TextButton
          name="검색"
          icon="mdi-check-bold"
          icon-color="info"
          font-size="1"
          @click="filterSubmit"
        />

        <TextButton
          name="초기화"
          icon="mdi-autorenew"
          icon-color="info"
          font-size="1"
          @click="resetFilter"
        />

        <TextButton
          name="검색양식 저장"
          icon="mdi-content-save"
          icon-color="indigo"
          font-size="1"
        />
      </slot>
    </CCol>
  </CRow>
</template>
