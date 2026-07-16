<script lang="ts" setup>
import { onBeforeMount, type PropType, reactive, ref, watch } from 'vue'
import type { selectProject } from '@/store/types/work_project.ts'
import type { IssueFilter, IssueStatus, Tracker } from '@/store/types/work_issue.ts'
import Multiselect from '@vueform/multiselect'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import { useAccount } from '@/store/pinia/account'
import AllProjectsSelect from '@/views/_Work/components/atomics/AllProjectsSelect.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

const props = defineProps({
  allProjects: { type: Array as PropType<selectProject[]>, default: () => [] },
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
    ],
    disabled: true,
  },
  {
    label: '날짜별 검색',
    options: [
      { value: 'created', label: '\u00A0\u00A0\u00A0등록일', disabled: true },
      { value: 'updated', label: '\u00A0\u00A0\u00A0변경일', disabled: true },
      { value: 'start_date', label: '\u00A0\u00A0\u00A0시작일', disabled: true },
      { value: 'due_date', label: '\u00A0\u00A0\u00A0완료기한', disabled: true },
    ],
    disabled: true,
  },
  {
    label: '파일',
    options: [
      { value: 'file', label: '\u00A0\u00A0\u00A0파일', disabled: true },
      { value: 'file_desc', label: '\u00A0\u00A0\u00A0파일설명', disabled: true },
    ],
    disabled: true,
  },
  {
    label: '담당',
    options: [
      { value: 'group', label: '\u00A0\u00A0\u00A0할당된 사람의 그룹', disabled: true },
      { value: 'role', label: '\u00A0\u00A0\u00A0할당된 사람의 역할', disabled: true },
    ],
  },
  {
    label: '목표단계',
    options: [
      { value: 'version_date', label: '\u00A0\u00A0\u00A0목표단계의 날짜', disabled: true },
      { value: 'version_status', label: '\u00A0\u00A0\u00A0목표단계의 상태', disabled: true },
    ],
    disabled: true,
  },
  {
    label: '관계',
    options: [
      { value: 'parent_issue', label: '\u00A0\u00A0\u00A0상위업무' },
      { value: 'parent', label: '\u00A0\u00A0\u00A0하위업무' },
      { value: 'follows_issue', label: '\u00A0\u00A0\u00A0선행업무' },
      { value: 'precedes_issue', label: '\u00A0\u00A0\u00A0후속업무' },
    ],
  },
])

const cond = ref({
  status: 'open' as 'open' | 'is' | 'exclude' | 'closed' | 'any',
  project: 'is' as 'is' | 'exclude',
  tracker: 'is' as 'is' | 'exclude',
  priority: 'is' as 'is' | 'exclude',
  category: 'is' as 'is' | 'exclude' | 'none' | 'any',
  is_private: 'is' as 'is' | 'exclude',
  watcher: 'is' as 'is' | 'exclude',
  done_ratio: 'is' as 'is' | 'gte' | 'lte' | 'between' | 'none' | 'any',
  author: 'is' as 'is' | 'exclude',
  updater: 'is' as 'is' | 'exclude',
  last_updater: 'is' as 'is' | 'exclude',
  assignee: 'is' as 'is' | 'exclude' | 'none' | 'any',
  // is_public: 'is' as 'is' | 'exclude',
  // name: 'contains',
  // description: 'contains',
  version: 'is' as 'is' | 'exclude' | 'none' | 'any',
  issue: 'is' as 'is' | 'gte' | 'lte' | 'between' | 'none' | 'any',
  parent: 'is' as 'is' | 'contains' | 'none' | 'any',
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
  id__any: '',
  parent__subject: '',
  parent__isnull: '0',
  parent_issue: null, // 상위업무
  parent: '' as string | number, // 하위업무
  follows_issue: null, // 선행업무
  precedes_issue: null, // 후속업무
  project__my_project: undefined,
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
    else if (cond.value.last_updater === 'exclude') filterData.last_updater__exclude = form.value.last_updater__exclude
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
    else if (cond.value.issue === 'between') filterData.id__between = form.value.id__between
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

  if (form.value.parent)
    if (cond.value.parent === 'is') filterData.parent = form.value.parent
    else if (cond.value.parent === 'contains')
      filterData.parent__subject = form.value.parent as string
    else if (cond.value.parent === 'none') filterData.parent__isnull = '1'
    else if (cond.value.parent === 'any') filterData.parent__isnull = '0'

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
  if (nVal.includes('last_updater') && !form.value.last_updater) form.value.last_updater = props.getUsers[0]?.value
  if (!nVal.includes('status')) searchCond.value = ['status']
})

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
                  :all-projects="allProjects"
                  default-title="<< 내 프로젝트 >>"
                  value-type="slug"
                  size="sm"
                />
              </CCol>
            </CRow>

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
                  <option value="any">모두</option>
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
                  v-model="form.id__between"
                  placeholder="10,20"
                  style="height: 30px"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <CRow v-if="searchCond.includes('parent_issue')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="상위업무" id="parent_issue" readonly />
              </CCol>
              <CCol class="col-8 col-lg-3">
                <Multiselect
                  v-model="form.parent_issue"
                  :options="getIssues"
                  placeholder="상위업무 선택"
                  searchable
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <CRow v-if="searchCond.includes('parent')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="하위업무" id="parent" readonly />
              </CCol>
              <CCol class="col-8 col-lg-3">
                <Multiselect
                  v-model="form.parent"
                  :options="getIssues"
                  placeholder="하위업무 선택"
                  searchable
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <CRow v-if="searchCond.includes('follows_issue')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="선행업무" id="follows_issue" readonly />
              </CCol>
              <CCol class="col-8 col-lg-3">
                <Multiselect
                  v-model="form.follows_issue"
                  :options="getIssues"
                  placeholder="선행업무 선택"
                  searchable
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <CRow v-if="searchCond.includes('precedes_issue')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="후속업무" id="precedes_issue" readonly />
              </CCol>
              <CCol class="col-8 col-lg-3">
                <Multiselect
                  v-model="form.precedes_issue"
                  :options="getIssues"
                  placeholder="후속업무 선택"
                  searchable
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
