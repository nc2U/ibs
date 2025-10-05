<script lang="ts" setup>
import { ref, reactive, type PropType, onBeforeMount, watch, computed } from 'vue'
import type { getProject, IssueProject } from '@/store/types/work_project.ts'
import type { IssueStatus, Tracker, TimeEntryFilter } from '@/store/types/work_issue.ts'
import { useRoute } from 'vue-router'
import { dateFormat } from '@/utils/baseMixins'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import IProjectSelect from '@/views/_Work/components/IProjectSelect.vue'

const props = defineProps({
  subProjects: { type: Array as PropType<IssueProject[]>, default: () => [] },
  allProjects: { type: Array as PropType<getProject[]>, default: () => [] },
  getIssues: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
  getMembers: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
  statusList: { type: Array as PropType<IssueStatus[]>, default: () => [] },
  trackerList: { type: Array as PropType<Tracker[]>, default: () => [] },
  getVersions: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
})

const emit = defineEmits(['filter-submit'])

const viewMode = ref<'board' | 'list'>('board')
const condVisible = ref(true)
const optVisible = ref(false)

const searchCond = ref(['spent_on'])
const resetFilter = () => {
  searchCond.value = ['spent_on']
  filterSubmit()
}

const searchOptions = reactive([
  {
    options: [
      { value: 'spent_on', label: '작업일자', disabled: true },
      { value: 'issue', label: '업무' },
      { value: 'user', label: '사용자' },
      { value: 'author', label: '저자', disabled: true },
      { value: 'activity', label: '작업종류', disabled: true },
      { value: 'hours', label: '시간', disabled: true },
    ],
  },
  {
    label: '문자열 검색',
    options: [{ value: 'comment', label: '설명' }],
    disabled: true,
  },
  {
    label: '업무',
    options: [
      { value: 'tracker', label: '업무의 유형', disabled: true },
      { value: 'parent', label: '업무의 상위업무', disabled: true },
      { value: 'status', label: '업무의 상태', disabled: true },
      { value: 'target_version', label: '업무의 목표버전' },
      { value: 'subject', label: '업무의 제목', disabled: true },
    ],
  },
  {
    label: '프로젝트',
    options: [{ value: 'project_status', label: '프로젝트의 상태', disabled: true }],
    disabled: true,
  },
])

const cond = ref({
  spent_on: 'any' as
    | 'is'
    | 'gte'
    | 'lte'
    | 'between'
    | 'before_days'
    | 'today'
    | 'yesterday'
    | 'this_week'
    | 'last_week'
    | 'this_month'
    | 'last_month'
    | 'this_year'
    | 'any',
  project: 'is' as 'is' | 'exclude',
  issue: 'is' as 'is' | 'keyword' | 'any',
  creator: 'is' as 'is' | 'exclude' | 'any',
  author: 'is' as 'is' | 'exclude' | 'none' | 'any',
  activity: 'is' as 'is' | 'exclude',
  hours: 'is' as 'is' | '>=' | '<=' | 'between' | 'none' | 'any',

  comment: 'contain' as 'contain' | 'start_with' | 'end_with' | 'none' | 'any',

  issue_tracker: 'is' as 'is' | 'exclude',
  issue_parent: 'is' as 'is' | 'keyword' | 'none' | 'any',
  issue_status: 'is' as 'is' | 'exclude',
  issue_target_version: 'is' as 'is' | 'exclude',
  issue_subject: 'contain' as 'contain' | 'start_with' | 'end_with' | 'none' | 'any',

  project_status: 'is' as 'is' | 'exclude',
})

const form = ref<TimeEntryFilter & { before_days: number | null }>({
  project: '',
  spent_on: '',
  from_spent_on: '',
  to_spent_on: '',
  before_days: null,
  issue: '',
  issue__keyword: '',
  creator: '',
  author: '',
  activity: '',
  comment: '',
  tracker: '',
  parent: '',
  status: '',
  version: '',
  subject: '',
  project_status: '',
})

const computedProjects = computed(() =>
  props.subProjects.length ? props.subProjects : props.allProjects,
)

const filterSubmit = () => {
  const filterData = {} as TimeEntryFilter

  const today = dateFormat(new Date())

  if (cond.value.spent_on === 'any') filterData.spent_on = ''
  else if (cond.value.spent_on === 'is') filterData.spent_on = form.value.spent_on
  else if (cond.value.spent_on === 'gte') filterData.from_spent_on = form.value.spent_on
  else if (cond.value.spent_on === 'lte') filterData.to_spent_on = form.value.spent_on
  else if (cond.value.spent_on === 'between') {
    filterData.from_spent_on = form.value.spent_on
    filterData.to_spent_on = form.value.to_spent_on
  } else if (cond.value.spent_on === 'before_days')
    filterData.spent_on = dateFormat(
      new Date(new Date(today).setDate(new Date(today).getDate() - (form.value.before_days ?? 0))),
    )
  else if (cond.value.spent_on === 'today') filterData.spent_on = today
  else if (cond.value.spent_on === 'yesterday')
    filterData.spent_on = dateFormat(
      new Date(new Date(today).setDate(new Date(today).getDate() - 1)),
    )
  // else if (cond.value.spent_on === 'this_week') filterData.spent_on = form.value.spent_on
  // else if (cond.value.spent_on === 'last_week') filterData.spent_on = form.value.spent_on
  // else if (cond.value.spent_on === 'this_month') filterData.spent_on = form.value.spent_on
  // else if (cond.value.spent_on === 'last_month') filterData.spent_on = form.value.spent_on
  // else if (cond.value.spent_on === 'this_year') filterData.spent_on = form.value.spent_on

  if (searchCond.value.includes('project'))
    if (cond.value.project === 'is') filterData.project__search = form.value.project
    else if (cond.value.project === 'exclude') filterData.project__exclude = form.value.project

  if (searchCond.value.includes('issue'))
    if (cond.value.issue === 'is') filterData.issue = form.value.issue
    else if (cond.value.issue === 'keyword') filterData.issue__keyword = form.value.issue__keyword
    else if (cond.value.issue === 'any') filterData.issue = ''

  if (searchCond.value.includes('user'))
    if (cond.value.creator === 'is') filterData.creator = form.value.creator
    else if (cond.value.creator === 'exclude') filterData.creator__exclude = form.value.creator
    else if (cond.value.creator === 'any') filterData.creator = ''

  if (searchCond.value.includes('target_version'))
    if (cond.value.issue_target_version === 'is') filterData.version = form.value.version
    else if (cond.value.creator === 'exclude') filterData.version__exclude = form.value.version

  // if (form.value.name) filterData.name = form.value.name
  // if (form.value.description) filterData.description = form.value.description

  emit('filter-submit', filterData)
}

watch(props, nVal => {
  if (!!nVal.statusList.length) form.value.status = props.statusList[0]?.pk
  if (!!nVal.subProjects.length && searchOptions[0].options.length === 6)
    searchOptions[0].options.splice(1, 0, { value: 'project', label: '하위 프로젝트' })
})

watch(searchCond, nVal => {
  if (nVal.includes('project')) form.value.project = computedProjects.value[0]?.slug
  if (nVal.includes('tracker')) form.value.tracker = props.trackerList[0]?.pk
  if (!nVal.includes('spent_on')) searchCond.value = ['spent_on']
})

const route = useRoute()

onBeforeMount(() => {
  if (!!props.statusList.length) form.value.status = props.statusList[0]?.pk

  if (route.name === '소요시간' && searchOptions[0].options.length === 6)
    searchOptions[0].options.splice(1, 0, { value: 'project', label: '프로젝트' })

  if (!!route.query.version) {
    searchCond.value.push('target_version')
    cond.value.issue_target_version = 'is'
    form.value.version = Number(route.query.version)
  }
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
                <CFormCheck label="작업일자" id="spent_on" checked="true" readonly />
              </CCol>
              <CCol class="d-none d-lg-block col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.spent_on" size="sm">
                  <option value="is">이다</option>
                  <option value="lte">이전(까지)</option>
                  <option value="gte">이후(부터)</option>
                  <option value="between">사이</option>
                  <option value="before_days">일 전</option>
                  <option value="today">오늘</option>
                  <option value="yesterday">어제</option>
                  <option value="this_week" disabled>이번 주</option>
                  <option value="last_week" disabled>지난 주</option>
                  <option value="this_month" disabled>이번 달</option>
                  <option value="last_month" disabled>지난 달</option>
                  <option value="this_year" disabled>올해</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-8 col-lg-3">
                <DatePicker
                  v-model="form.spent_on"
                  v-if="
                    cond.spent_on === 'is' ||
                    cond.spent_on === 'lte' ||
                    cond.spent_on === 'gte' ||
                    cond.spent_on === 'between'
                  "
                />

                <div v-show="cond.spent_on === 'before_days'">
                  <span class="col-sm-5" style="float: left">
                    <CFormInput
                      v-model.number="form.before_days"
                      type="number"
                      min="0"
                      maxlength="10"
                      id="before_days"
                      size="sm"
                    />
                  </span>
                  <span class="col-sm-5 pl-2">일</span>
                </div>
              </CCol>
              <CCol v-show="cond.spent_on === 'between'" class="col-8 col-lg-3">
                <DatePicker v-model="form.to_spent_on" />
              </CCol>
            </CRow>

            <CRow v-if="searchCond.includes('project')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck
                  checked="true"
                  :label="subProjects.length ? '하위 프로젝트' : '프로젝트'"
                  id="project"
                  readonly
                />
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

            <CRow v-if="searchCond.includes('issue')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="업무" id="issue" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.issue" size="sm">
                  <option value="is">이다</option>
                  <option value="keyword">포함되는 키워드</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>

              <CCol class="col-4 col-lg-3">
                <Multiselect
                  v-if="cond.issue === 'is'"
                  v-model="form.issue"
                  :options="getIssues"
                  searchable
                  placeholder="업무 선택"
                />
                <CFormInput
                  v-if="cond.issue === 'keyword'"
                  v-model="form.issue__keyword"
                  tooltip-feedback
                  placeholder="업무 키워드"
                  @keydown.enter="filterSubmit"
                />
              </CCol>
            </CRow>

            <CRow v-if="searchCond.includes('user')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="사용자" id="user" readonly />
              </CCol>
              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.creator" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4 col-lg-3">
                <Multiselect
                  v-if="cond.creator === 'is' || cond.creator === 'exclude'"
                  v-model="form.creator"
                  :options="getMembers"
                  placeholder="사용자 선택"
                  searchable
                />
              </CCol>
            </CRow>

            <CRow v-if="searchCond.includes('target_version')">
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck checked="true" label="업무의 목표버전" id="issue_version" readonly />
              </CCol>

              <CCol class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.issue_target_version" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>

              <CCol class="col-4 col-lg-3">
                <Multiselect
                  v-if="cond.issue_target_version"
                  v-model="form.version"
                  :options="getVersions"
                  placeholder="버전 선택"
                  searchable
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
