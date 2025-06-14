<script lang="ts" setup>
import { ref, reactive, type PropType, onBeforeMount, watch } from 'vue'
import type { IssueProject } from '@/store/types/work_project.ts'
import type { IssueStatus, IssueFilter, Tracker } from '@/store/types/work_issue.ts'
import { useRoute } from 'vue-router'
import Multiselect from '@vueform/multiselect'
import IProjectSelect from '@/views/_Work/components/IProjectSelect.vue'

const props = defineProps({
  allProjects: { type: Array as PropType<IssueProject[]>, default: () => [] },
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
      { value: 'version', label: '목표버전' },
      { value: 'category', label: '범주', disabled: true },
      { value: 'done_ratio', label: '진척도', disabled: true },
      { value: 'is_private', label: '비공개', disabled: true },
      { value: 'watcher', label: '업무관람자', disabled: true },
      { value: 'updater', label: '수정자', disabled: true },
      { value: 'last_updater', label: '최근수정자', disabled: true },
      { value: 'issue', label: '업무', disabled: true },
    ],
  },
  {
    label: '문자열 검색',
    options: [
      { value: 'subject', label: '제목' },
      { value: 'description', label: '설명' },
      { value: 'comment', label: '댓글' },
    ],
    disabled: true,
  },
  {
    label: '날짜별 검색',
    options: [
      { value: 'created', label: '등록일', disabled: true },
      { value: 'updated', label: '변경일', disabled: true },
      { value: 'start_date', label: '시작일', disabled: true },
      { value: 'due_date', label: '완료기한', disabled: true },
    ],
    disabled: true,
  },
  {
    label: '시간추적',
    options: [
      { value: 'estimated_hours', label: '추정시간', disabled: true },
      { value: 'spent_time', label: '소요시간', disabled: true },
    ],
    disabled: true,
  },
  {
    label: '파일',
    options: [
      { value: 'file', label: '파일', disabled: true },
      { value: 'file_desc', label: '파일설명', disabled: true },
    ],
    disabled: true,
  },
  {
    label: '담당',
    options: [
      { value: 'group', label: '할당된 사람의 그룹', disabled: true },
      { value: 'role', label: '할당된 사람의 역할', disabled: true },
    ],
  },
  {
    label: '목표버전',
    options: [
      { value: 'version_date', label: '목표버전의 날짜', disabled: true },
      { value: 'version_status', label: '목표버전의 상태', disabled: true },
    ],
    disabled: true,
  },
  {
    label: '관계',
    options: [
      { value: 'related_to', label: '다음 업무와 관련됨:', disabled: true },
      { value: 'is_duplicate_of', label: '다음 업무와 중복됨:', disabled: true },
      { value: 'has_duplicate', label: '중복된 업무:', disabled: true },
      { value: 'blocks', label: '다음 업무의 해결을 막고 있음:', disabled: true },
      { value: 'blocked_by', label: '다음 업무에 막혀 있음:', disabled: true },
      { value: 'precedes', label: '다음에 진행할 업무:', disabled: true },
      { value: 'follows', label: '다음 업무를 우선 진행:', disabled: true },
      { value: 'copied_to', label: '다음 업무로 복사됨:', disabled: true },
      { value: 'copied_from', label: '다음 업무로부터 복사됨:', disabled: true },
      { value: 'parent', label: '상위업무' },
      { value: 'sub_issues', label: '하위업무', disabled: true },
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

  parent: 'is' as 'is' | 'contains' | 'none' | 'any',
})

const route = useRoute()
const form = ref<IssueFilter>({
  status: null,
  status__exclude: null,
  project: (route.params.projId as string) ?? '',
  tracker: null,
  tracker__exclude: null,
  author: null,
  author__exclude: null,
  assignee: null,
  assignee__exclude: null,

  // name: '',
  // description: '',

  version: null,
  parent: '' as string | number,
})

const filterSubmit = () => {
  const filterData = { project: form.value.project } as IssueFilter

  if (cond.value.status === 'open') filterData.status__closed = '0'
  else if (cond.value.status === 'is') filterData.status = form.value.status
  else if (cond.value.status === 'exclude') filterData.status__exclude = form.value.status
  else if (cond.value.status === 'closed') filterData.status__closed = '1'
  else if (cond.value.status === 'any') filterData.status__closed = ''

  if (searchCond.value.includes('project'))
    if (cond.value.project === 'is') filterData.project__search = form.value.project
    else if (cond.value.project === 'exclude') filterData.project__exclude = form.value.project

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

  // if (cond.value.is_public === 'is' && searchCond.value.includes('is_public'))
  //   filterData.is_public = form.value.is_public
  // else if (cond.value.is_public === 'exclude' && searchCond.value.includes('is_public'))
  //   filterData.is_public__exclude = form.value.is_public
  // if (form.value.name) filterData.name = form.value.name

  if (searchCond.value.includes('version'))
    if (cond.value.version === 'is') filterData.version = form.value.version
    else if (cond.value.version === 'exclude') filterData.version__exclude = form.value.version
    else if (cond.value.version === 'none') filterData.version__isnull = '1'
    else if (cond.value.version === 'any') filterData.version__isnull = '0'

  if (form.value.parent)
    if (cond.value.parent === 'is') filterData.parent = form.value.parent
    else if (cond.value.parent === 'contains')
      filterData.parent__subject = form.value.parent as string
    else if (cond.value.parent === 'none') filterData.parent__isnull = '1'
    else if (cond.value.parent === 'any') filterData.parent__isnull = '0'

  emit('filter-submit', filterData)
}

watch(props, nVal => {
  if (nVal.statusList.length) form.value.status = props.statusList[0]?.pk
})

watch(searchCond, nVal => {
  if (nVal.includes('project')) form.value.project = props.allProjects[0]?.slug
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
                <IProjectSelect v-model="form.project" :all-projects="allProjects" size="sm" />
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
                <CFormCheck checked="true" label="목표버전" id="version" readonly />
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
                  placeholder="목표버전"
                  searchable
                  size="sm"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!--            <CRow v-if="searchCond.includes('is_public')">-->
            <!--              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">-->
            <!--                <CFormCheck checked="true" label="공개여부" id="is_public" readonly />-->
            <!--              </CCol>-->
            <!--              <CCol class="col-4 col-lg-3 col-xl-2">-->
            <!--                <CFormSelect v-model="cond.is_public" size="sm">-->
            <!--                  <option value="is">is</option>-->
            <!--                  <option value="exclude">is not</option>-->
            <!--                </CFormSelect>-->
            <!--              </CCol>-->
            <!--              <CCol class="col-4 col-lg-3">-->
            <!--                <CFormSelect v-model="form.is_public" size="sm">-->
            <!--                  <option value="1">예</option>-->
            <!--                  <option value="0">아니오</option>-->
            <!--                </CFormSelect>-->
            <!--              </CCol>-->
            <!--            </CRow>-->

            <!--            <CRow v-if="searchCond.includes('created')">-->
            <!--              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">-->
            <!--                <CFormCheck checked="true" label="등록일자" id="created" readonly />-->
            <!--              </CCol>-->
            <!--              <CCol class="col-4 col-lg-3 col-xl-2">-->
            <!--                <CFormSelect size="sm">-->
            <!--                  <option value="1">is</option>-->
            <!--                  <option value="2">&gt;=</option>-->
            <!--                  <option value="3">&lt;=</option>-->
            <!--                  <option value="4">between</option>-->
            <!--                  <option value="5">less than days ago</option>-->
            <!--                  <option value="6">more than days ago</option>-->
            <!--                  <option value="7">is the past</option>-->
            <!--                  <option value="8">days ago</option>-->
            <!--                  <option value="9">today</option>-->
            <!--                  <option value="10">yesterday</option>-->
            <!--                  <option value="11">this week</option>-->
            <!--                  <option value="12">last week</option>-->
            <!--                  <option value="13">last 2 weeks</option>-->
            <!--                  <option value="14">this month</option>-->
            <!--                  <option value="15">last month</option>-->
            <!--                  <option value="16">this year</option>-->
            <!--                  <option value="17">none</option>-->
            <!--                  <option value="18">any</option>-->
            <!--                </CFormSelect>-->
            <!--              </CCol>-->
            <!--              <CCol class="col-4 col-lg-3 col-xl-2">-->
            <!--                <DatePicker size="sm" />-->
            <!--              </CCol>-->
            <!--            </CRow>-->

            <CRow v-if="searchCond.includes('parent')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="상위업무" id="parent" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.parent" size="sm">
                  <option value="is">이다</option>
                  <option value="contains">포함되는 키워드</option>
                  <option value="none">없음</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>
              <CCol
                v-if="cond.parent === 'is' || cond.parent === 'contains'"
                class="col-4 col-lg-3"
              >
                <Multiselect
                  v-if="cond.parent === 'is'"
                  v-model="form.parent"
                  :options="getIssues"
                  placeholder="상위 업무"
                  searchable
                  size="sm"
                  @keydown.enter="filterSubmit"
                />
                <CFormInput
                  v-if="cond.parent === 'contains'"
                  v-model="form.parent"
                  size="sm"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <!--            <CRow v-if="searchCond.includes('description')">-->
            <!--              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">-->
            <!--                <CFormCheck checked="true" label="설명" id="description" readonly />-->
            <!--              </CCol>-->
            <!--              <CCol class="col-4 col-lg-3 col-xl-2">-->
            <!--                <CFormSelect v-model="cond.description" size="sm">-->
            <!--                  <option value="contains">contains</option>-->
            <!--                  <option value="2">contains any of</option>-->
            <!--                  <option value="3">doesn't contain</option>-->
            <!--                  <option value="4">starts with</option>-->
            <!--                  <option value="5">ends with</option>-->
            <!--                  <option value="6">none</option>-->
            <!--                  <option value="7">any</option>-->
            <!--                </CFormSelect>-->
            <!--              </CCol>-->
            <!--              <CCol class="col-4 col-lg-3">-->
            <!--                <CFormInput v-model="form.description" size="sm" />-->
            <!--              </CCol>-->
            <!--            </CRow>-->
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
        <v-icon icon="mdi-check-bold" size="sm" color="success" class="mr-1" />
        <router-link to="" class="mr-3" @click="filterSubmit">검색</router-link>
        <v-icon icon="mdi-replay" size="sm" color="success" class="mr-1" />
        <router-link to="" class="mr-3" @click="resetFilter">초기화</router-link>
        <!--        <router-link to=""> Save 검색양식</router-link>-->
      </slot>
    </CCol>
  </CRow>
</template>
