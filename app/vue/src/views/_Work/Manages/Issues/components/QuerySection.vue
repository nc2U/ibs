<script lang="ts" setup>
import { onBeforeMount, type PropType, reactive, ref, watch, computed } from 'vue'
import type { selectProject } from '@/store/types/work_project.ts'
import type { IssueFilter, IssueStatus, Tracker } from '@/store/types/work_issue.ts'
import Multiselect from '@vueform/multiselect'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import { useAccount } from '@/store/pinia/account'
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
const accStore = useAccount()
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

const cond = ref({
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
const form = ref<IssueFilter>({
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

const filterSubmit = () => {
  const filterData = {} as IssueFilter

  // 기본 프로젝트 조회 (project__slug) 세팅
  if (form.value.project) {
    filterData.project__slug = form.value.project
  }

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

  if (searchCond.value.includes('project')) {
    if (form.value.project === '') {
      if (cond.value.project === 'is') {
        filterData.project__my_project = true
      } else if (cond.value.project === 'exclude') {
        filterData.project__my_project = false
      }
      delete filterData.project__slug
    } else {
      if (cond.value.project === 'is') {
        filterData.project__search = form.value.project
      } else if (cond.value.project === 'exclude') {
        filterData.project__exclude = form.value.project
        // 제외 조건일 경우 기본 포함(project__slug) 조건과의 충돌을 방지하기 위해 제거
        delete filterData.project__slug
      }
    }
  }

  if (form.value.project__my_project !== undefined) {
    filterData.project__my_project = form.value.project__my_project
  }

  if (searchCond.value.includes('tracker'))
    if (cond.value.tracker === 'is') filterData.tracker = form.value.tracker
    else if (cond.value.tracker === 'exclude') filterData.tracker__exclude = form.value.tracker

  if (searchCond.value.includes('priority'))
    if (cond.value.priority === 'is') filterData.priority = form.value.priority
    else if (cond.value.priority === 'exclude') filterData.priority__exclude = form.value.priority

  if (searchCond.value.includes('category'))
    if (cond.value.category === 'is') filterData.category = form.value.category
    else if (cond.value.category === 'exclude') filterData.category__exclude = form.value.category
    else if (cond.value.category === 'none') filterData.category__isnull = '1'
    else if (cond.value.category === 'any') filterData.category__isnull = '0'

  if (searchCond.value.includes('is_private')) {
    if (cond.value.is_private === 'is') filterData.is_private = true
    else if (cond.value.is_private === 'exclude') filterData.is_private = false
  }

  if (searchCond.value.includes('watcher')) {
    if (cond.value.watcher === 'is') filterData.watcher = form.value.watcher
    else if (cond.value.watcher === 'exclude') filterData.watcher__exclude = form.value.watcher
  }

  if (searchCond.value.includes('author'))
    if (cond.value.author === 'is') filterData.author = form.value.author
    else if (cond.value.author === 'exclude') filterData.author__exclude = form.value.author

  if (searchCond.value.includes('updater')) {
    if (cond.value.updater === 'is') filterData.updater = form.value.updater
    else if (cond.value.updater === 'exclude') filterData.updater__exclude = form.value.updater
  }

  if (searchCond.value.includes('last_updater')) {
    if (cond.value.last_updater === 'is') filterData.last_updater = form.value.last_updater
    else if (cond.value.last_updater === 'exclude')
      filterData.last_updater__exclude = form.value.last_updater__exclude
  }

  if (searchCond.value.includes('assignee'))
    if (cond.value.assignee === 'is') filterData.assignee = form.value.assignee
    else if (cond.value.assignee === 'exclude') filterData.assignee__exclude = form.value.assignee
    else if (cond.value.assignee === 'none') filterData.assignee__isnull = '1'
    else if (cond.value.assignee === 'any') filterData.assignee__isnull = '0'

  if (searchCond.value.includes('version'))
    if (cond.value.version === 'is') filterData.version = form.value.version
    else if (cond.value.version === 'exclude') filterData.version__exclude = form.value.version
    else if (cond.value.version === 'none') filterData.version__isnull = '1'
    else if (cond.value.version === 'any') filterData.version__isnull = '0'

  if (searchCond.value.includes('issue')) {
    if (cond.value.issue === 'is') filterData.id = form.value.id
    else if (cond.value.issue === 'gte') filterData.id__gte = form.value.id__gte
    else if (cond.value.issue === 'lte') filterData.id__lte = form.value.id__lte
    else if (cond.value.issue === 'between') {
      const min =
        form.value.id__between_min !== null && form.value.id__between_min !== undefined
          ? form.value.id__between_min
          : ''
      const max =
        form.value.id__between_max !== null && form.value.id__between_max !== undefined
          ? form.value.id__between_max
          : ''
      if (min !== '' || max !== '') {
        filterData.id__between = `${min},${max}`
      }
    }
  }

  if (searchCond.value.includes('subject')) {
    if (cond.value.subject === 'contains') filterData.subject = form.value.subject
    else if (cond.value.subject === 'exclude')
      filterData.subject__exclude = form.value.subject__exclude
  }

  if (searchCond.value.includes('description')) {
    if (cond.value.description === 'contains') filterData.description = form.value.description
    else if (cond.value.description === 'exclude')
      filterData.description__exclude = form.value.description__exclude
  }

  if (searchCond.value.includes('comment')) {
    if (cond.value.comment === 'contains') filterData.comment = form.value.comment
    else if (cond.value.comment === 'exclude')
      filterData.comment__exclude = form.value.comment__exclude
  }

  if (searchCond.value.includes('any_searchable')) {
    if (cond.value.any_searchable === 'contains')
      filterData.any_searchable = form.value.any_searchable
    else if (cond.value.any_searchable === 'exclude')
      filterData.any_searchable__exclude = form.value.any_searchable__exclude
  }

  if (searchCond.value.includes('file')) {
    if (cond.value.file === 'contains') filterData.file = form.value.file
    else if (cond.value.file === 'exclude') filterData.file__exclude = form.value.file__exclude
  }

  if (searchCond.value.includes('file_desc')) {
    if (cond.value.file_desc === 'contains') filterData.file_desc = form.value.file_desc
    else if (cond.value.file_desc === 'exclude')
      filterData.file_desc__exclude = form.value.file_desc__exclude
  }

  if (searchCond.value.includes('creator_role')) {
    if (cond.value.creator_role === 'is') filterData.creator_role = form.value.creator_role
    else if (cond.value.creator_role === 'exclude')
      filterData.creator_role__exclude = form.value.creator_role__exclude
  }

  if (searchCond.value.includes('assignee_role')) {
    if (cond.value.assignee_role === 'is') filterData.assignee_role = form.value.assignee_role
    else if (cond.value.assignee_role === 'exclude')
      filterData.assignee_role__exclude = form.value.assignee_role__exclude
  }

  // version_date
  if (searchCond.value.includes('version_date')) {
    if (cond.value.version_date === 'is') filterData.version_date = form.value.version_date
    else if (cond.value.version_date === 'gte')
      filterData.version_date__gte = form.value.version_date__gte
    else if (cond.value.version_date === 'lte')
      filterData.version_date__lte = form.value.version_date__lte
    else if (cond.value.version_date === 'between') {
      const min = form.value.version_date__between_min || ''
      const max = form.value.version_date__between_max || ''
      if (min || max) filterData.version_date__between = `${min},${max}`
    } else if (cond.value.version_date === 'none') filterData.version_date__isnull = '1'
    else if (cond.value.version_date === 'any') filterData.version_date__isnull = '0'
  }

  // version_status
  if (searchCond.value.includes('version_status')) {
    if (cond.value.version_status === 'is') filterData.version_status = form.value.version_status
    else if (cond.value.version_status === 'exclude')
      filterData.version_status__exclude = form.value.version_status__exclude
  }

  // project_status
  if (searchCond.value.includes('project_status')) {
    if (cond.value.project_status === 'is') filterData.project_status = form.value.project_status
    else if (cond.value.project_status === 'exclude')
      filterData.project_status__exclude = form.value.project_status__exclude
  }

  // sub_project
  if (searchCond.value.includes('sub_project')) {
    if (cond.value.sub_project === 'any') filterData.sub_project__isnull = '0'
    else if (cond.value.sub_project === 'none') filterData.sub_project__isnull = '1'
    else if (cond.value.sub_project === 'is') filterData.sub_project = form.value.sub_project
    else if (cond.value.sub_project === 'exclude')
      filterData.sub_project__exclude = form.value.sub_project__exclude
  }

  // follows_issue
  if (searchCond.value.includes('follows_issue')) {
    if (cond.value.follows_issue === 'is') filterData.follows_issue = form.value.follows_issue
    else if (cond.value.follows_issue === 'exclude')
      filterData.follows_issue__exclude = form.value.follows_issue__exclude
    else if (cond.value.follows_issue === 'none') filterData.follows_issue__isnull = '1'
    else if (cond.value.follows_issue === 'any') filterData.follows_issue__isnull = '0'
  }

  // precedes_issue
  if (searchCond.value.includes('precedes_issue')) {
    if (cond.value.precedes_issue === 'is') filterData.precedes_issue = form.value.precedes_issue
    else if (cond.value.precedes_issue === 'exclude')
      filterData.precedes_issue__exclude = form.value.precedes_issue__exclude
    else if (cond.value.precedes_issue === 'none') filterData.precedes_issue__isnull = '1'
    else if (cond.value.precedes_issue === 'any') filterData.precedes_issue__isnull = '0'
  }

  // parent_issue
  if (searchCond.value.includes('parent_issue')) {
    if (cond.value.parent_issue === 'is') filterData.parent_issue = form.value.parent_issue
    else if (cond.value.parent_issue === 'exclude')
      filterData.parent_issue__exclude = form.value.parent_issue__exclude
    else if (cond.value.parent_issue === 'contains')
      filterData.parent_issue__contains = form.value.parent_issue__contains
    else if (cond.value.parent_issue === 'none') filterData.parent_issue__isnull = '1'
    else if (cond.value.parent_issue === 'any') filterData.parent_issue__isnull = '0'
  }

  // parent (sub_issue)
  if (searchCond.value.includes('sub_issue')) {
    if (cond.value.parent === 'is') filterData.parent = form.value.parent
    else if (cond.value.parent === 'exclude')
      filterData.parent__exclude = form.value.parent__exclude
    else if (cond.value.parent === 'contains')
      filterData.parent__contains = form.value.parent__contains
    else if (cond.value.parent === 'none') filterData.parent__isnull = '1'
    else if (cond.value.parent === 'any') filterData.parent__isnull = '0'
  }

  // created
  if (searchCond.value.includes('created')) {
    if (cond.value.created === 'is') filterData.created = form.value.created
    else if (cond.value.created === 'gte') filterData.created__gte = form.value.created__gte
    else if (cond.value.created === 'lte') filterData.created__lte = form.value.created__lte
    else if (cond.value.created === 'between') {
      const min = form.value.created__between_min || ''
      const max = form.value.created__between_max || ''
      if (min || max) filterData.created__between = `${min},${max}`
    }
  }

  // updated
  if (searchCond.value.includes('updated')) {
    if (cond.value.updated === 'is') filterData.updated = form.value.updated
    else if (cond.value.updated === 'gte') filterData.updated__gte = form.value.updated__gte
    else if (cond.value.updated === 'lte') filterData.updated__lte = form.value.updated__lte
    else if (cond.value.updated === 'between') {
      const min = form.value.updated__between_min || ''
      const max = form.value.updated__between_max || ''
      if (min || max) filterData.updated__between = `${min},${max}`
    }
  }

  // start_date
  if (searchCond.value.includes('start_date')) {
    if (cond.value.start_date === 'is') filterData.start_date = form.value.start_date
    else if (cond.value.start_date === 'gte')
      filterData.start_date__gte = form.value.start_date__gte
    else if (cond.value.start_date === 'lte')
      filterData.start_date__lte = form.value.start_date__lte
    else if (cond.value.start_date === 'between') {
      const min = form.value.start_date__between_min || ''
      const max = form.value.start_date__between_max || ''
      if (min || max) filterData.start_date__between = `${min},${max}`
    }
  }

  // due_date
  if (searchCond.value.includes('due_date')) {
    if (cond.value.due_date === 'is') filterData.due_date = form.value.due_date
    else if (cond.value.due_date === 'gte') filterData.due_date__gte = form.value.due_date__gte
    else if (cond.value.due_date === 'lte') filterData.due_date__lte = form.value.due_date__lte
    else if (cond.value.due_date === 'between') {
      const min = form.value.due_date__between_min || ''
      const max = form.value.due_date__between_max || ''
      if (min || max) filterData.due_date__between = `${min},${max}`
    } else if (cond.value.due_date === 'none') filterData.due_date__isnull = '1'
    else if (cond.value.due_date === 'any') filterData.due_date__isnull = '0'
  }

  if (searchCond.value.includes('done_ratio')) {
    if (cond.value.done_ratio === 'is') filterData.done_ratio = form.value.done_ratio
    else if (cond.value.done_ratio === 'gte')
      filterData.done_ratio__gte = form.value.done_ratio__gte
    else if (cond.value.done_ratio === 'lte')
      filterData.done_ratio__lte = form.value.done_ratio__lte
    else if (cond.value.done_ratio === 'between') {
      const min =
        form.value.done_ratio__between_min !== null &&
        form.value.done_ratio__between_min !== undefined
          ? form.value.done_ratio__between_min
          : ''
      const max =
        form.value.done_ratio__between_max !== null &&
        form.value.done_ratio__between_max !== undefined
          ? form.value.done_ratio__between_max
          : ''
      if (min !== '' || max !== '') {
        filterData.done_ratio__between = `${min},${max}`
      }
    } else if (cond.value.done_ratio === 'none') filterData.done_ratio__isnull = '1'
    else if (cond.value.done_ratio === 'any') filterData.done_ratio__isnull = '0'
  }

  console.log(filterData)

  emit('filter-submit', filterData)
}

watch(
  () => props.statusList,
  nVal => {
    if (nVal.length && !form.value.status) form.value.status = nVal[0]?.pk
  },
  { immediate: true },
)

watch(
  () => props.trackerList,
  nVal => {
    if (nVal.length && !form.value.tracker) form.value.tracker = nVal[0]?.pk
  },
  { immediate: true },
)

watch(
  () => props.priorityList,
  nVal => {
    if (nVal.length && !form.value.priority) form.value.priority = nVal[0]?.pk
  },
  { immediate: true },
)

watch(
  () => props.categoryList,
  nVal => {
    if (nVal.length && !form.value.category) form.value.category = nVal[0]?.pk
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

const subProjects = computed(() => workStore.currentProject?.sub_projects || [])

const hasSubProjects = computed(() => subProjects.value.length > 0)

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

  // 비공개 업무 권한 검사 (수퍼유저/관리자 혹은 issue.private 권한)
  const canPrivate = accStore.workManager || can(PERM.ISSUE_PRIVATE)
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

            <!-- 프로젝트 (project) -->
            <CRow v-if="searchCond.includes('project')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="프로젝트" id="project" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.project" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <AllProjectsSelect
                  v-model="form.project"
                  :search-projects="searchProjects"
                  default-title="<< 내 프로젝트 >>"
                  value-type="slug"
                  size="sm"
                />
              </CCol>
            </CRow>

            <!-- 유형 (tracker) -->
            <CRow v-if="searchCond.includes('tracker')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="유형" id="tracker" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.tracker" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <CFormSelect v-model="form.tracker" size="sm">
                  <option v-for="tracker in trackerList" :key="tracker.pk" :value="tracker.pk">
                    {{ tracker.name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>

            <!-- 우선순위 (priority) -->
            <CRow v-if="searchCond.includes('priority')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="우선순위" id="priority" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.priority" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <CFormSelect v-model="form.priority" size="sm">
                  <option v-for="priority in priorityList" :key="priority.pk" :value="priority.pk">
                    {{ priority.name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>

            <!-- 작성자 (author) -->
            <CRow v-if="searchCond.includes('author')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="작성자" id="author" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.author" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <Multiselect
                  v-model="form.author"
                  :options="getUsers"
                  placeholder="작성자"
                  searchable
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!-- 담당자 (assignee) -->
            <CRow v-if="searchCond.includes('assignee')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="담당자" id="assignee" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.assignee" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                  <option value="none">없음</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <Multiselect
                  v-if="cond.assignee === 'is' || cond.assignee === 'exclude'"
                  v-model="form.assignee"
                  :options="getUsers"
                  placeholder="담당자"
                  searchable
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!-- 목표단계 (version) -->
            <CRow v-if="searchCond.includes('version')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="목표단계" id="version" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.version" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                  <option value="none">없음</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <Multiselect
                  v-if="cond.version === 'is' || cond.version === 'exclude'"
                  v-model="form.version"
                  :options="getVersions"
                  placeholder="목표단계"
                  searchable
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!-- 범주 (category) -->
            <CRow v-if="searchCond.includes('category')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="범주" id="category" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.category" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                  <option value="none">없음</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <CFormSelect
                  v-if="cond.category === 'is' || cond.category === 'exclude'"
                  v-model="form.category"
                  size="sm"
                >
                  <option v-for="category in categoryList" :key="category.pk" :value="category.pk">
                    {{ category.name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>

            <!-- 진척도 (tracker) -->
            <CRow v-if="searchCond.includes('done_ratio')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="진척도" id="done_ratio" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.done_ratio" size="sm">
                  <option value="is">이다</option>
                  <option value="gte">&gt;=</option>
                  <option value="lte">&lt;=</option>
                  <option value="between">사이</option>
                  <option value="none">없음</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <CFormInput
                  v-if="cond.done_ratio === 'is'"
                  v-model="form.done_ratio"
                  type="number"
                  placeholder="진척도 (%)"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.done_ratio === 'gte'"
                  v-model="form.done_ratio__gte"
                  type="number"
                  placeholder="이상 (%)"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.done_ratio === 'lte'"
                  v-model="form.done_ratio__lte"
                  type="number"
                  placeholder="이하 (%)"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.done_ratio === 'between'"
                  v-model="form.done_ratio__between_min"
                  type="number"
                  placeholder="최소 (%)"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
              </CCol>

              <CCol v-if="cond.done_ratio === 'between'" class="col-4 col-lg-3">
                <CFormInput
                  v-model="form.done_ratio__between_max"
                  type="number"
                  placeholder="최대 (%)"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!-- 비공개 (is_private) -->
            <CRow v-if="searchCond.includes('is_private')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="비공개" id="is_private" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.is_private" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3"> </CCol>
            </CRow>

            <!-- 업무 관람자 (watcher) -->
            <CRow v-if="searchCond.includes('watcher')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="업무관람자" id="watcher" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.watcher" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <Multiselect
                  v-model="form.watcher"
                  :options="getUsers"
                  placeholder="업무관람자"
                  searchable
                  size="sm"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!-- 수정자 (updater) -->
            <CRow v-if="searchCond.includes('updater')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="수정자" id="updater" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.updater" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <Multiselect
                  v-model="form.updater"
                  :options="getUsers"
                  placeholder="수정자"
                  searchable
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!-- 최근 수정자 (Last_updater) -->
            <CRow v-if="searchCond.includes('last_updater')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="최근수정자" id="last_updater" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.last_updater" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <Multiselect
                  v-model="form.last_updater"
                  :options="getUsers"
                  placeholder="최근수정자"
                  searchable
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!-- 하위 프로젝트 (sub_project) -->
            <CRow v-if="searchCond.includes('sub_project') && hasSubProjects">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="하위 프로젝트" id="sub_project" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.sub_project" size="sm" @change="filterSubmit">
                  <option value="any">모두</option>
                  <option value="none">없음</option>
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
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
              </CCol>
            </CRow>

            <!-- 프로젝트의 상태 (project_status) -->
            <CRow v-if="searchCond.includes('project_status')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="프로젝트의 상태" id="project_status" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.project_status" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <CFormSelect
                  v-if="cond.project_status === 'is'"
                  v-model="form.project_status"
                  size="sm"
                  @change="filterSubmit"
                >
                  <option value="1">사용중</option>
                  <option value="2">닫힘</option>
                </CFormSelect>
                <CFormSelect
                  v-if="cond.project_status === 'exclude'"
                  v-model="form.project_status__exclude"
                  size="sm"
                  @change="filterSubmit"
                >
                  <option value="1">사용중</option>
                  <option value="2">닫힘</option>
                </CFormSelect>
              </CCol>
            </CRow>

            <!-- 업무 (issue) -->
            <CRow v-if="searchCond.includes('issue')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="업무" id="issue" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.issue" size="sm">
                  <option value="is">이다</option>
                  <option value="gte">&gt;=</option>
                  <option value="lte">&lt;=</option>
                  <option value="between">사이</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3" id="issue-search">
                <CFormInput
                  v-if="cond.issue === 'is'"
                  v-model="form.id"
                  placeholder="ID"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.issue === 'gte'"
                  v-model="form.id__gte"
                  placeholder="이상"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.issue === 'lte'"
                  v-model="form.id__lte"
                  placeholder="이하"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.issue === 'between'"
                  v-model="form.id__between_min"
                  type="number"
                  placeholder="최소 ID"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
              <CCol v-if="cond.issue === 'between'" class="col-4 col-lg-3">
                <CFormInput
                  v-model="form.id__between_max"
                  type="number"
                  placeholder="최대 ID"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!-- 제목 (subject) -->
            <CRow v-if="searchCond.includes('subject')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="제목" id="subject" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.subject" size="sm">
                  <option value="contains">포함되는 키워드</option>
                  <option value="exclude">포함하지 않는 키워드</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <CFormInput
                  v-if="cond.subject === 'contains'"
                  v-model="form.subject"
                  placeholder="제목 키워드"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.subject === 'exclude'"
                  v-model="form.subject__exclude"
                  placeholder="제외할 제목 키워드"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!-- 설명 (description) -->
            <CRow v-if="searchCond.includes('description')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="설명" id="description" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.description" size="sm">
                  <option value="contains">포함되는 키워드</option>
                  <option value="exclude">포함하지 않는 키워드</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <CFormInput
                  v-if="cond.description === 'contains'"
                  v-model="form.description"
                  placeholder="설명 키워드"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.description === 'exclude'"
                  v-model="form.description__exclude"
                  placeholder="제외할 설명 키워드"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!-- 댓글 (comment) -->
            <CRow v-if="searchCond.includes('comment')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="댓글" id="comment" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.comment" size="sm">
                  <option value="contains">포함되는 키워드</option>
                  <option value="exclude">포함하지 않는 키워드</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <CFormInput
                  v-if="cond.comment === 'contains'"
                  v-model="form.comment"
                  placeholder="댓글 키워드"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.comment === 'exclude'"
                  v-model="form.comment__exclude"
                  placeholder="제외할 댓글 키워드"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!-- 전체 내용 (any_searchable) -->
            <CRow v-if="searchCond.includes('any_searchable')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="전체 내용" id="any_searchable" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.any_searchable" size="sm">
                  <option value="contains">포함되는 키워드</option>
                  <option value="exclude">포함하지 않는 키워드</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <CFormInput
                  v-if="cond.any_searchable === 'contains'"
                  v-model="form.any_searchable"
                  placeholder="검색 키워드 (제목, 설명, 댓글)"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.any_searchable === 'exclude'"
                  v-model="form.any_searchable__exclude"
                  placeholder="제외할 검색 키워드"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!-- 등록일 (created) -->
            <CRow v-if="searchCond.includes('created')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="등록일" id="created" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.created" size="sm">
                  <option value="is">이다</option>
                  <option value="lte">이전</option>
                  <option value="gte">이후</option>
                  <option value="between">사이</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <DatePicker
                  v-if="cond.created === 'is'"
                  v-model="form.created"
                  placeholder="등록일"
                  @update:model-value="filterSubmit"
                />
                <DatePicker
                  v-if="cond.created === 'lte'"
                  v-model="form.created__lte"
                  placeholder="이전"
                  @update:model-value="filterSubmit"
                />
                <DatePicker
                  v-if="cond.created === 'gte'"
                  v-model="form.created__gte"
                  placeholder="이후"
                  @update:model-value="filterSubmit"
                />
                <div v-if="cond.created === 'between'" class="d-flex align-items-center">
                  <DatePicker
                    v-model="form.created__between_min"
                    placeholder="시작일"
                    @update:model-value="filterSubmit"
                  />
                  <span class="mx-2">~</span>
                  <DatePicker
                    v-model="form.created__between_max"
                    placeholder="종료일"
                    @update:model-value="filterSubmit"
                  />
                </div>
              </CCol>
            </CRow>

            <!-- 변경일 (updated) -->
            <CRow v-if="searchCond.includes('updated')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="변경일" id="updated" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.updated" size="sm">
                  <option value="is">이다</option>
                  <option value="lte">이전</option>
                  <option value="gte">이후</option>
                  <option value="between">사이</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <DatePicker
                  v-if="cond.updated === 'is'"
                  v-model="form.updated"
                  placeholder="변경일"
                  @update:model-value="filterSubmit"
                />
                <DatePicker
                  v-if="cond.updated === 'lte'"
                  v-model="form.updated__lte"
                  placeholder="이전"
                  @update:model-value="filterSubmit"
                />
                <DatePicker
                  v-if="cond.updated === 'gte'"
                  v-model="form.updated__gte"
                  placeholder="이후"
                  @update:model-value="filterSubmit"
                />
                <div v-if="cond.updated === 'between'" class="d-flex align-items-center">
                  <DatePicker
                    v-model="form.updated__between_min"
                    placeholder="시작일"
                    @update:model-value="filterSubmit"
                  />
                  <span class="mx-2">~</span>
                  <DatePicker
                    v-model="form.updated__between_max"
                    placeholder="종료일"
                    @update:model-value="filterSubmit"
                  />
                </div>
              </CCol>
            </CRow>

            <!-- 시작일 (start_date) -->
            <CRow v-if="searchCond.includes('start_date')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="시작일" id="start_date" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.start_date" size="sm">
                  <option value="is">이다</option>
                  <option value="lte">이전</option>
                  <option value="gte">이후</option>
                  <option value="between">사이</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <DatePicker
                  v-if="cond.start_date === 'is'"
                  v-model="form.start_date"
                  placeholder="시작일"
                  @update:model-value="filterSubmit"
                />
                <DatePicker
                  v-if="cond.start_date === 'lte'"
                  v-model="form.start_date__lte"
                  placeholder="이전"
                  @update:model-value="filterSubmit"
                />
                <DatePicker
                  v-if="cond.start_date === 'gte'"
                  v-model="form.start_date__gte"
                  placeholder="이후"
                  @update:model-value="filterSubmit"
                />
                <div v-if="cond.start_date === 'between'" class="d-flex align-items-center">
                  <DatePicker
                    v-model="form.start_date__between_min"
                    placeholder="시작일"
                    @update:model-value="filterSubmit"
                  />
                  <span class="mx-2">~</span>
                  <DatePicker
                    v-model="form.start_date__between_max"
                    placeholder="종료일"
                    @update:model-value="filterSubmit"
                  />
                </div>
              </CCol>
            </CRow>

            <!-- 완료기한 (due_date) -->
            <CRow v-if="searchCond.includes('due_date')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="완료기한" id="due_date" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.due_date" size="sm">
                  <option value="is">이다</option>
                  <option value="lte">이전</option>
                  <option value="gte">이후</option>
                  <option value="between">사이</option>
                  <option value="none">없음</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <DatePicker
                  v-if="cond.due_date === 'is'"
                  v-model="form.due_date"
                  placeholder="완료기한"
                  @update:model-value="filterSubmit"
                />
                <DatePicker
                  v-if="cond.due_date === 'lte'"
                  v-model="form.due_date__lte"
                  placeholder="이전"
                  @update:model-value="filterSubmit"
                />
                <DatePicker
                  v-if="cond.due_date === 'gte'"
                  v-model="form.due_date__gte"
                  placeholder="이후"
                  @update:model-value="filterSubmit"
                />
                <div v-if="cond.due_date === 'between'" class="d-flex align-items-center">
                  <DatePicker
                    v-model="form.due_date__between_min"
                    placeholder="시작일"
                    @update:model-value="filterSubmit"
                  />
                  <span class="mx-2">~</span>
                  <DatePicker
                    v-model="form.due_date__between_max"
                    placeholder="종료일"
                    @update:model-value="filterSubmit"
                  />
                </div>
              </CCol>
            </CRow>

            <!-- 파일 (file) -->
            <CRow v-if="searchCond.includes('file')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="파일" id="file" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.file" size="sm">
                  <option value="contains">포함되는 키워드</option>
                  <option value="exclude">포함하지 않는 키워드</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <CFormInput
                  v-if="cond.file === 'contains'"
                  v-model="form.file"
                  placeholder="파일명 키워드"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.file === 'exclude'"
                  v-model="form.file__exclude"
                  placeholder="제외할 파일명 키워드"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!-- 파일설명 (file_desc) -->
            <CRow v-if="searchCond.includes('file_desc')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="파일설명" id="file_desc" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.file_desc" size="sm">
                  <option value="contains">포함되는 키워드</option>
                  <option value="exclude">포함하지 않는 키워드</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <CFormInput
                  v-if="cond.file_desc === 'contains'"
                  v-model="form.file_desc"
                  placeholder="파일설명 키워드"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.file_desc === 'exclude'"
                  v-model="form.file_desc__exclude"
                  placeholder="제외할 파일설명 키워드"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!-- 작성자 역할 (creator_role) -->
            <CRow v-if="searchCond.includes('creator_role')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="작성자의 역할" id="creator_role" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.creator_role" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <CFormSelect
                  v-if="cond.creator_role === 'is'"
                  v-model="form.creator_role"
                  size="sm"
                  @change="filterSubmit"
                >
                  <option v-for="r in roleList" :key="r.pk" :value="r.pk">
                    {{ r.name }}
                  </option>
                </CFormSelect>
                <CFormSelect
                  v-if="cond.creator_role === 'exclude'"
                  v-model="form.creator_role__exclude"
                  size="sm"
                  @change="filterSubmit"
                >
                  <option v-for="r in roleList" :key="r.pk" :value="r.pk">
                    {{ r.name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>

            <!-- 담당자 역할 (assignee_role) -->
            <CRow v-if="searchCond.includes('assignee_role')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="담당자의 역할" id="assignee_role" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.assignee_role" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <CFormSelect
                  v-if="cond.assignee_role === 'is'"
                  v-model="form.assignee_role"
                  size="sm"
                  @change="filterSubmit"
                >
                  <option v-for="r in roleList" :key="r.pk" :value="r.pk">
                    {{ r.name }}
                  </option>
                </CFormSelect>
                <CFormSelect
                  v-if="cond.assignee_role === 'exclude'"
                  v-model="form.assignee_role__exclude"
                  size="sm"
                  @change="filterSubmit"
                >
                  <option v-for="r in roleList" :key="r.pk" :value="r.pk">
                    {{ r.name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>

            <!-- 목표단계의 날짜 (version_date) -->
            <CRow v-if="searchCond.includes('version_date')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="목표단계의 날짜" id="version_date" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.version_date" size="sm">
                  <option value="is">이다</option>
                  <option value="lte">이내</option>
                  <option value="gte">이후</option>
                  <option value="between">사이</option>
                  <option value="none">없음</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <DatePicker
                  v-if="cond.version_date === 'is'"
                  v-model="form.version_date"
                  placeholder="목표단계 완료 기한"
                  @update:model-value="filterSubmit"
                />
                <DatePicker
                  v-if="cond.version_date === 'lte'"
                  v-model="form.version_date__lte"
                  placeholder="이내"
                  @update:model-value="filterSubmit"
                />
                <DatePicker
                  v-if="cond.version_date === 'gte'"
                  v-model="form.version_date__gte"
                  placeholder="이후"
                  @update:model-value="filterSubmit"
                />
                <div v-if="cond.version_date === 'between'" class="d-flex align-items-center">
                  <DatePicker
                    v-model="form.version_date__between_min"
                    placeholder="시작일"
                    @update:model-value="filterSubmit"
                  />
                  <span class="mx-2">~</span>
                  <DatePicker
                    v-model="form.version_date__between_max"
                    placeholder="종료일"
                    @update:model-value="filterSubmit"
                  />
                </div>
              </CCol>
            </CRow>

            <!-- 목표단계의 상태 (version_status) -->
            <CRow v-if="searchCond.includes('version_status')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="목표단계의 상태" id="version_status" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.version_status" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <CFormSelect
                  v-if="cond.version_status === 'is'"
                  v-model="form.version_status"
                  size="sm"
                  @change="filterSubmit"
                >
                  <option value="1">진행</option>
                  <option value="2">잠김</option>
                  <option value="3">닫힘</option>
                </CFormSelect>
                <CFormSelect
                  v-if="cond.version_status === 'exclude'"
                  v-model="form.version_status__exclude"
                  size="sm"
                  @change="filterSubmit"
                >
                  <option value="1">진행</option>
                  <option value="2">잠김</option>
                  <option value="3">닫힘</option>
                </CFormSelect>
              </CCol>
            </CRow>

            <!-- 후속 업무 (follows_issue) -->
            <CRow v-if="searchCond.includes('follows_issue')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="선행업무" id="follows_issue" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.follows_issue" size="sm" @change="filterSubmit">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                  <option value="none">없음</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <CFormInput
                  v-if="cond.follows_issue === 'is'"
                  v-model.number="form.follows_issue"
                  type="number"
                  placeholder="선행업무 ID 입력"
                  size="sm"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.follows_issue === 'exclude'"
                  v-model.number="form.follows_issue__exclude"
                  type="number"
                  placeholder="선행업무 ID 입력"
                  size="sm"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!-- 선행 업무 (precedes_issue) -->
            <CRow v-if="searchCond.includes('precedes_issue')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="후속업무" id="precedes_issue" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.precedes_issue" size="sm" @change="filterSubmit">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                  <option value="none">없음</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <CFormInput
                  v-if="cond.precedes_issue === 'is'"
                  v-model.number="form.precedes_issue"
                  type="number"
                  placeholder="후속업무 ID 입력"
                  size="sm"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.precedes_issue === 'exclude'"
                  v-model.number="form.precedes_issue__exclude"
                  type="number"
                  placeholder="후속업무 ID 입력"
                  size="sm"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!-- 상위 업무 (parent_issue) -->
            <CRow v-if="searchCond.includes('parent_issue')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="상위업무" id="parent_issue" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.parent_issue" size="sm" @change="filterSubmit">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                  <option value="contains">포함되는 키워드</option>
                  <option value="none">없음</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <CFormInput
                  v-if="cond.parent_issue === 'is'"
                  v-model.number="form.parent_issue"
                  type="number"
                  placeholder="상위업무 ID 입력"
                  size="sm"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.parent_issue === 'exclude'"
                  v-model.number="form.parent_issue__exclude"
                  type="number"
                  placeholder="상위업무 ID 입력"
                  size="sm"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.parent_issue === 'contains'"
                  v-model="form.parent_issue__contains"
                  placeholder="제목 키워드 입력"
                  size="sm"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!-- 하위 업무 (sub_issue) -->
            <CRow v-if="searchCond.includes('sub_issue')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="하위업무" id="parent" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.parent" size="sm" @change="filterSubmit">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                  <option value="contains">포함되는 키워드</option>
                  <option value="none">없음</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <CFormInput
                  v-if="cond.parent === 'is'"
                  v-model.number="form.parent"
                  type="number"
                  placeholder="하위업무 ID 입력"
                  size="sm"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.parent === 'exclude'"
                  v-model.number="form.parent__exclude"
                  type="number"
                  placeholder="하위업무 ID 입력"
                  size="sm"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.parent === 'contains'"
                  v-model="form.parent__contains"
                  placeholder="제목 키워드 입력"
                  size="sm"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>
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
