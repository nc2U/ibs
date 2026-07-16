<script lang="ts" setup>
import { onBeforeMount, type PropType, reactive, ref, watch } from 'vue'
import type { selectProject } from '@/store/types/work_project.ts'
import type { IssueFilter, IssueStatus, Tracker } from '@/store/types/work_issue.ts'
import { useRoute } from 'vue-router'
import Multiselect from '@vueform/multiselect'
import AllProjectsSelect from '@/views/_Work/components/atomics/AllProjectsSelect.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

const props = defineProps({
  allProjects: { type: Array as PropType<selectProject[]>, default: () => [] },
  statusList: { type: Array as PropType<IssueStatus[]>, default: () => [] },
  trackerList: { type: Array as PropType<Tracker[]>, default: () => [] },
  getIssues: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
  getUsers: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
  getVersions: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
})

const emit = defineEmits(['filter-submit'])

const viewMode = ref<'board' | 'list'>('board')
const condVisible = ref(true)
const optVisible = ref(false)

const searchCond = ref(['status'])
const resetFilter = () => {
  searchCond.value = ['status']
  filterSubmit()
}

const searchOptions = reactive([
  {
    options: [
      { value: 'status', label: '상태', disabled: true },
      { value: 'tracker', label: '유형' },
      { value: 'priority', label: '우선순위', disabled: true },
      { value: 'author', label: '작성자' },
      { value: 'assignee', label: '담당자' },
      { value: 'version', label: '목표단계' },
      { value: 'category', label: '범주', disabled: true },
      { value: 'done_ratio', label: '진척도', disabled: true },
      { value: 'is_private', label: '비공개', disabled: true },
      { value: 'watcher', label: '업무관람자', disabled: true },
      { value: 'updater', label: '수정자', disabled: true },
      { value: 'last_updater', label: '최근수정자', disabled: true },
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
  author: 'is' as 'is' | 'exclude',
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
  author: null,
  author__exclude: null,
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

  if (searchCond.value.includes('author'))
    if (cond.value.author === 'is') filterData.author = form.value.author
    else if (cond.value.author === 'exclude') filterData.author__exclude = form.value.author

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

  if (form.value.parent)
    if (cond.value.parent === 'is') filterData.parent = form.value.parent
    else if (cond.value.parent === 'contains')
      filterData.parent__subject = form.value.parent as string
    else if (cond.value.parent === 'none') filterData.parent__isnull = '1'
    else if (cond.value.parent === 'any') filterData.parent__isnull = '0'

  console.log(filterData)

  emit('filter-submit', filterData)
}

watch(props, nVal => {
  if (nVal.statusList.length) form.value.status = props.statusList[0]?.pk
})

watch(searchCond, nVal => {
  if (nVal.includes('project')) form.value.project = ''
  if (nVal.includes('tracker')) form.value.tracker = props.trackerList[0]?.pk
  if (!nVal.includes('status')) searchCond.value = ['status']
})

onBeforeMount(async () => {
  if (!!props.statusList.length) form.value.status = props.statusList[0]?.pk
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
                  size="sm"
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
                  size="sm"
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
                  size="sm"
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
                  size="sm"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.issue === 'gte'"
                  v-model="form.id__gte"
                  placeholder="이상"
                  size="sm"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.issue === 'lte'"
                  v-model="form.id__lte"
                  placeholder="이하"
                  size="sm"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.issue === 'between'"
                  v-model="form.id__between"
                  placeholder="10,20"
                  size="sm"
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
                  size="sm"
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
                  size="sm"
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
                  size="sm"
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
                  size="sm"
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
