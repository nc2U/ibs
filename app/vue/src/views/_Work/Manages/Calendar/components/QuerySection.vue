<script lang="ts" setup>
import { computed, onMounted, type PropType, reactive, ref, watch } from 'vue'
import type { selectProject } from '@/store/types/work_project.ts'
import type { IssueStatus, Tracker } from '@/store/types/work_issue.ts'
import type { MeetingCategory } from '@/store/types/work_meeting.ts'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import IssueProjectSelector from '@/views/_Work/components/atomics/IssueProjectSelector.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import SaveQueryModal from '@/views/_Work/components/SaveQueryModal.vue'
import { usePerms } from '@/composables/usePerms'

import { useRoute } from 'vue-router'

const route = useRoute()
const { can, PERM } = usePerms()

// ----- Props -----
const props = defineProps({
  searchProjects: { type: Array as PropType<selectProject[]>, default: () => [] },
  statusList: { type: Array as PropType<IssueStatus[]>, default: () => [] },
  trackerList: { type: Array as PropType<Tracker[]>, default: () => [] },
  priorityList: { type: Array as PropType<any[]>, default: () => [] },
  meetingCategories: { type: Array as PropType<MeetingCategory[]>, default: () => [] },
  getUsers: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
  targetType: {
    type: String as PropType<'project' | 'calendar' | 'issue' | 'meeting'>,
    default: 'calendar',
  },
})

const emit = defineEmits(['filter-submit'])

const refQuerySaveModal = ref()
const openSaveModal = () => {
  refQuerySaveModal.value?.callModal()
}

// ----- 표시 상태 -----
const condVisible = ref(true)

// ----- 이벤트 종류 선택 (업무 / 회의 표시 토글) -----
const eventTypes = ref<('issue' | 'meeting')[]>(['issue', 'meeting'])

// ----- 검색조건 추가 (태그 기반 동적 추가 조건) -----
const searchCond = ref<string[]>(['issue_status'])

// searchOptions 에서 고정(disabled) 항목들은 언제나 표시됨
// 'issue_status' 는 고정 조건 (is_status)
const searchOptions = reactive([
  ...(route.params.projId
    ? []
    : [
        {
          label: '공통',
          options: [{ value: 'project', label: '프로젝트' }],
        },
      ]),
  {
    label: '업무 조건',
    options: [
      { value: 'issue_status', label: '  업무 상태' },
      { value: 'tracker', label: '  유형' },
      { value: 'priority', label: '  우선순위' },
      { value: 'assignee', label: '  담당자' },
      { value: 'author', label: '  작성자' },
      { value: 'issue_subject', label: '  제목 키워드' },
      { value: 'start_date', label: '  시작일' },
      { value: 'due_date', label: '  완료기한' },
    ],
  },
  {
    label: '회의 조건',
    options: [
      { value: 'meeting_status', label: '  회의 상태' },
      { value: 'meeting_category', label: '  카테고리' },
      { value: 'meeting_attendees', label: '  참석자' },
      { value: 'meeting_creator', label: '  작성자' },
      { value: 'meeting_title', label: '  제목 키워드' },
      { value: 'meeting_date', label: '  회의일 기간' },
    ],
  },
])

// ----- 각 조건의 연산자 상태 -----
const cond = ref<Record<string, any>>({
  issue_status: 'open' as 'open' | 'is' | 'exclude' | 'closed' | 'any',
  project: 'is' as 'is' | 'exclude',
  tracker: 'is' as 'is' | 'exclude',
  priority: 'is' as 'is' | 'exclude',
  assignee: 'is' as 'is' | 'exclude',
  author: 'is' as 'is' | 'exclude',
  issue_subject: 'contains' as 'contains' | 'exclude',
  start_date: 'gte' as 'is' | 'gte' | 'lte' | 'between',
  due_date: 'lte' as 'is' | 'gte' | 'lte' | 'between',
  meeting_status: 'is' as 'is' | 'exclude',
  meeting_category: 'is' as 'is' | 'exclude',
  meeting_attendees: 'is' as 'is' | 'exclude',
  meeting_creator: 'is' as 'is' | 'exclude',
  meeting_title: 'contains' as 'contains' | 'exclude',
  meeting_date: 'between' as 'is' | 'gte' | 'lte' | 'between',
})

// ----- 폼 값 상태 -----
const form = ref<Record<string, any>>({
  // 공통
  project: '',

  // 업무 조건
  issue_status: null,
  issue_status__exclude: null,
  tracker: null,
  tracker__exclude: null,
  priority: null,
  priority__exclude: null,
  assignee: null,
  assignee__exclude: null,
  author: null,
  author__exclude: null,
  issue_subject: '',
  issue_subject__exclude: '',
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

  // 회의 조건
  meeting_status: '1',
  meeting_status__exclude: null,
  meeting_category: null,
  meeting_category__exclude: null,
  meeting_attendees: null,
  meeting_attendees__exclude: null,
  meeting_creator: null,
  meeting_creator__exclude: null,
  meeting_title: '',
  meeting_date: '',
  meeting_date__gte: '',
  meeting_date__lte: '',
  meeting_date__between_min: '',
  meeting_date__between_max: '',
})

// ----- 활성화된 필터 키 관리 (체크박스로 ON/OFF 가능) -----
// searchCond: 드롭다운 목록에 추가되어 폼에 렌더링된 항목들
// enabledFields: 그 중 체크박스가 [v] 선택되어 실제 검색 조건에 반영되는 항목들
const enabledFields = ref<string[]>(['issue_status'])

// searchCond 에 새 항목 추가 시 enabledFields 에도 자동 추가
watch(searchCond, (newVal) => {
  newVal.forEach(key => {
    if (!enabledFields.value.includes(key)) {
      enabledFields.value.push(key)
    }
  })
  // searchCond 에서 제거된 항목은 enabledFields 에서도 제거
  enabledFields.value = enabledFields.value.filter(k => newVal.includes(k))
})

const toggleField = (key: string, e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.checked) {
    if (!enabledFields.value.includes(key)) enabledFields.value.push(key)
  } else {
    enabledFields.value = enabledFields.value.filter(k => k !== key)
  }
  filterSubmit()
}

// ----- 동적 추가 조건 필터 목록 (searchCond에 등록된 모든 필드) -----
const filterFieldsConfig = computed(() => [
  ...(route.params.projId
    ? []
    : [
        {
          key: 'project',
          label: '프로젝트',
          type: 'project',
          condOptions: [
            { value: 'is', label: '이다' },
            { value: 'exclude', label: '아니다' },
          ],
        },
      ]),
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
    key: 'assignee',
    label: '담당자',
    type: 'multiselect',
    placeholder: '담당자 선택',
    condOptions: [
      { value: 'is', label: '이다' },
      { value: 'exclude', label: '아니다' },
    ],
    options: props.getUsers,
  },
  {
    key: 'author',
    label: '작성자 (업무)',
    type: 'multiselect',
    placeholder: '작성자 선택',
    condOptions: [
      { value: 'is', label: '이다' },
      { value: 'exclude', label: '아니다' },
    ],
    options: props.getUsers,
  },
  {
    key: 'issue_subject',
    label: '제목 (업무)',
    type: 'text-match',
    placeholder: '업무 제목 키워드',
    condOptions: [
      { value: 'contains', label: '포함되는 키워드' },
      { value: 'exclude', label: '포함하지 않는 키워드' },
    ],
  },
  {
    key: 'start_date',
    label: '시작일 (업무)',
    type: 'date',
    condOptions: [
      { value: 'is', label: '이다' },
      { value: 'gte', label: '이후' },
      { value: 'lte', label: '이전' },
      { value: 'between', label: '사이' },
    ],
  },
  {
    key: 'due_date',
    label: '완료기한 (업무)',
    type: 'date',
    condOptions: [
      { value: 'is', label: '이다' },
      { value: 'gte', label: '이후' },
      { value: 'lte', label: '이전' },
      { value: 'between', label: '사이' },
    ],
  },
  {
    key: 'meeting_status',
    label: '상태 (회의)',
    type: 'select',
    condOptions: [
      { value: 'is', label: '이다' },
      { value: 'exclude', label: '아니다' },
    ],
    options: [
      { value: '1', label: '준비' },
      { value: '2', label: '종료' },
      { value: '3', label: '취소' },
    ],
  },
  {
    key: 'meeting_category',
    label: '카테고리 (회의)',
    type: 'select',
    condOptions: [
      { value: 'is', label: '이다' },
      { value: 'exclude', label: '아니다' },
    ],
    options: props.meetingCategories.map(c => ({ value: c.pk, label: c.name })),
  },
  {
    key: 'meeting_attendees',
    label: '참석자 (회의)',
    type: 'multiselect',
    placeholder: '참석자 선택',
    condOptions: [
      { value: 'is', label: '이다' },
      { value: 'exclude', label: '아니다' },
    ],
    options: props.getUsers,
  },
  {
    key: 'meeting_creator',
    label: '작성자 (회의)',
    type: 'multiselect',
    placeholder: '작성자 선택',
    condOptions: [
      { value: 'is', label: '이다' },
      { value: 'exclude', label: '아니다' },
    ],
    options: props.getUsers,
  },
  {
    key: 'meeting_title',
    label: '제목 (회의)',
    type: 'text-match',
    placeholder: '회의 제목 키워드',
    condOptions: [
      { value: 'contains', label: '포함되는 키워드' },
      { value: 'exclude', label: '포함하지 않는 키워드' },
    ],
  },
  {
    key: 'meeting_date',
    label: '회의일',
    type: 'date',
    condOptions: [
      { value: 'is', label: '이다' },
      { value: 'gte', label: '이후' },
      { value: 'lte', label: '이전' },
      { value: 'between', label: '사이' },
    ],
  },
])

const activeFields = computed(() =>
  filterFieldsConfig.value.filter(f => searchCond.value.includes(f.key)),
)

// ----- filterSubmit: 통합 필터 객체 emit -----
const filterSubmit = () => {
  const payload: Record<string, any> = {
    event_type: eventTypes.value.length === 2 ? 'all' : eventTypes.value[0] ?? 'all',
  }

  // 프로젝트 (체크 박스 활성화시에만 적용)
  if (enabledFields.value.includes('project') && form.value.project) {
    if (cond.value.project === 'is') payload.project = form.value.project
    else if (cond.value.project === 'exclude') payload.project__exclude = form.value.project
  }

  // ===== 업무(Issue) 필터 =====
  // 업무 상태 (체크 박스 활성화시에만 적용)
  if (enabledFields.value.includes('issue_status')) {
    if (cond.value.issue_status === 'open') {
      payload.status__closed = '0'
    } else if (cond.value.issue_status === 'closed') {
      payload.status__closed = '1'
    } else if (cond.value.issue_status === 'any') {
      payload.status__closed = ''
    } else if (cond.value.issue_status === 'is' && form.value.issue_status) {
      payload.status = form.value.issue_status
      payload.status__closed = ''
    } else if (cond.value.issue_status === 'exclude' && form.value.issue_status__exclude) {
      payload.status__exclude = form.value.issue_status__exclude
      payload.status__closed = ''
    }
  }

  // 동적 조건 순회 (enabledFields 에 활성화된 키만 검색 파라미터에 반영)
  enabledFields.value.forEach(key => {
    if (key === 'issue_status' || key === 'project') return

    const op = cond.value[key]

    // 업무 필터
    if (key === 'tracker') {
      if (op === 'is' && form.value.tracker) payload.tracker = form.value.tracker
      else if (op === 'exclude' && form.value.tracker) payload.tracker__exclude = form.value.tracker
    } else if (key === 'priority') {
      if (op === 'is' && form.value.priority) payload.priority = form.value.priority
      else if (op === 'exclude' && form.value.priority) payload.priority__exclude = form.value.priority
    } else if (key === 'assignee') {
      if (op === 'is' && form.value.assignee) payload.assigned_to = form.value.assignee
      else if (op === 'exclude' && form.value.assignee) payload.assigned_to__exclude = form.value.assignee
    } else if (key === 'author') {
      if (op === 'is' && form.value.author) payload.creator = form.value.author
      else if (op === 'exclude' && form.value.author) payload.creator__exclude = form.value.author
    } else if (key === 'issue_subject') {
      if (op === 'contains' && form.value.issue_subject) payload.subject = form.value.issue_subject
      else if (op === 'exclude' && form.value.issue_subject__exclude) payload.subject__exclude = form.value.issue_subject__exclude
    } else if (key === 'start_date') {
      _applyDateFilter(payload, 'start_date', op)
    } else if (key === 'due_date') {
      _applyDateFilter(payload, 'due_date', op)

    // ===== 회의(Meeting) 필터 =====
    } else if (key === 'meeting_status') {
      if (op === 'is' && form.value.meeting_status) payload.meeting_status = form.value.meeting_status
      else if (op === 'exclude' && form.value.meeting_status) payload.meeting_status__exclude = form.value.meeting_status
    } else if (key === 'meeting_category') {
      if (op === 'is' && form.value.meeting_category) payload.meeting_category = form.value.meeting_category
      else if (op === 'exclude' && form.value.meeting_category) payload.meeting_category__exclude = form.value.meeting_category
    } else if (key === 'meeting_attendees') {
      if (op === 'is' && form.value.meeting_attendees) payload.meeting_attendees = form.value.meeting_attendees
      else if (op === 'exclude' && form.value.meeting_attendees) payload.meeting_attendees__exclude = form.value.meeting_attendees
    } else if (key === 'meeting_creator') {
      if (op === 'is' && form.value.meeting_creator) payload.meeting_creator = form.value.meeting_creator
      else if (op === 'exclude' && form.value.meeting_creator) payload.meeting_creator__exclude = form.value.meeting_creator
    } else if (key === 'meeting_title') {
      if (op === 'contains' && form.value.meeting_title) payload.meeting_search = form.value.meeting_title
      else if (op === 'exclude' && form.value.meeting_title__exclude) payload.meeting_search__exclude = form.value.meeting_title__exclude
    } else if (key === 'meeting_date') {
      _applyDateFilter(payload, 'meeting_date', op)
    }
  })

  emit('filter-submit', payload)
}

// 날짜 필터 공통 헬퍼
const _applyDateFilter = (payload: Record<string, any>, key: string, op: string) => {
  if (op === 'is' && form.value[key]) {
    payload[key] = form.value[key]
  } else if (op === 'gte' && form.value[`${key}__gte`]) {
    payload[`${key}__gte`] = form.value[`${key}__gte`]
  } else if (op === 'lte' && form.value[`${key}__lte`]) {
    payload[`${key}__lte`] = form.value[`${key}__lte`]
  } else if (op === 'between') {
    if (form.value[`${key}__between_min`]) payload[`${key}__gte`] = form.value[`${key}__between_min`]
    if (form.value[`${key}__between_max`]) payload[`${key}__lte`] = form.value[`${key}__between_max`]
  }
}

// ----- 초기화 -----
const resetFilter = () => {
  eventTypes.value = ['issue', 'meeting']
  searchCond.value = ['issue_status']
  enabledFields.value = ['issue_status']
  cond.value.issue_status = 'open'
  Object.keys(form.value).forEach(k => {
    if (typeof form.value[k] === 'string') form.value[k] = ''
    else form.value[k] = null
  })
  form.value.meeting_status = '1'
  filterSubmit()
}

// 업무 상태 변경 시 즉시 제출
watch(() => cond.value.issue_status, filterSubmit)
// 이벤트 종류 체크박스 변경 시 즉시 제출
watch(eventTypes, filterSubmit)

// props 초기값 반영
watch(
  () => props.statusList,
  list => {
    if (list.length && !form.value.issue_status) form.value.issue_status = list[0]?.pk
  },
  { immediate: true },
)
watch(
  () => props.trackerList,
  list => {
    if (list.length && !form.value.tracker) form.value.tracker = list[0]?.pk
  },
  { immediate: true },
)
watch(
  () => props.priorityList,
  list => {
    if (list.length && !form.value.priority) form.value.priority = list[0]?.pk
  },
  { immediate: true },
)
watch(
  () => props.meetingCategories,
  list => {
    if (list.length && !form.value.meeting_category) form.value.meeting_category = list[0]?.pk
  },
  { immediate: true },
)

onMounted(() => filterSubmit())

defineExpose({ resetFilter })
</script>

<template>
  <CRow>
    <CCol class="pointer pt-1 mb-0" @click="condVisible = !condVisible">
      <v-icon :icon="condVisible ? 'mdi-chevron-down' : 'mdi-chevron-right'" size="sm" />
      검색조건
    </CCol>
    <v-divider class="mx-3 mt-2 mb-0" />

    <CCollapse :visible="condVisible">
      <CRow class="m-2" color="light">
        <CCol class="col-12 col-md-8">

          <!-- 고정 1: 이벤트 종류 선택 -->
          <CRow class="mb-3">
            <CCol class="col-4 col-lg-3 col-xl-2 pt-1">
              <span class="form-check-label text-muted small fw-semibold">표시</span>
            </CCol>
            <CCol class="col-8 col-lg-6 d-flex align-items-center gap-3">
              <CFormCheck
                id="evt-issue"
                v-model="eventTypes"
                value="issue"
                label="업무"
                inline
              />
              <CFormCheck
                id="evt-meeting"
                v-model="eventTypes"
                value="meeting"
                label="회의"
                inline
              />
            </CCol>
          </CRow>

          <!-- 고정 2: 업무 상태 -->
          <CRow>
            <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
              <CFormCheck
                label="업무 상태"
                id="issue_status"
                :checked="enabledFields.includes('issue_status')"
                @change="toggleField('issue_status', $event)"
              />
            </CCol>
            <CCol
              v-if="enabledFields.includes('issue_status')"
              class="d-none d-lg-block col-4 col-lg-3 col-xl-2"
            >
              <CFormSelect v-model="cond.issue_status" size="sm">
                <option value="open">진행중</option>
                <option value="is">이다</option>
                <option value="exclude">아니다</option>
                <option value="closed">완료됨</option>
                <option value="any">모두</option>
              </CFormSelect>
            </CCol>
            <CCol v-if="enabledFields.includes('issue_status')" class="col-8 col-lg-3">
              <CFormSelect
                v-if="cond.issue_status === 'is' || cond.issue_status === 'exclude'"
                v-model="form.issue_status"
                size="sm"
              >
                <option v-for="s in statusList" :key="s.pk" :value="s.pk">{{ s.name }}</option>
              </CFormSelect>
            </CCol>
          </CRow>

          <!-- 동적 추가 조건 -->
          <template v-for="field in activeFields" :key="field.key">
            <CRow>
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck
                  :label="field.label"
                  :id="field.key"
                  :checked="enabledFields.includes(field.key)"
                  @change="toggleField(field.key, $event)"
                />
              </CCol>
              <CCol v-if="enabledFields.includes(field.key)" class="col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond[field.key]" size="sm">
                  <option v-for="opt in field.condOptions" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </option>
                </CFormSelect>
              </CCol>
              <CCol v-if="enabledFields.includes(field.key)" class="col-4 col-lg-3">

                <!-- 프로젝트 -->
                <template v-if="field.type === 'project'">
                  <IssueProjectSelector
                    v-model="form.project"
                    :issue-project-list="searchProjects"
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
                  >
                    <option v-for="opt in (field as any).options" :key="opt.value" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </CFormSelect>
                </template>

                <!-- 멀티셀렉트 -->
                <template v-else-if="field.type === 'multiselect'">
                  <Multiselect
                    v-if="cond[field.key] === 'is'"
                    v-model="form[field.key]"
                    :options="(field as any).options"
                    :placeholder="(field as any).placeholder"
                    searchable
                    @keydown.enter="filterSubmit"
                  />
                  <Multiselect
                    v-else-if="cond[field.key] === 'exclude'"
                    v-model="form[`${field.key}__exclude`]"
                    :options="(field as any).options"
                    :placeholder="(field as any).placeholder"
                    searchable
                    @keydown.enter="filterSubmit"
                  />
                </template>

                <!-- 텍스트 매칭 -->
                <template v-else-if="field.type === 'text-match'">
                  <CFormInput
                    v-if="cond[field.key] === 'contains'"
                    v-model="form[field.key]"
                    :placeholder="(field as any).placeholder"
                    style="height: 30px"
                    @keydown.enter="filterSubmit"
                  />
                  <CFormInput
                    v-else-if="cond[field.key] === 'exclude'"
                    v-model="form[`${field.key}__exclude`]"
                    :placeholder="'제외할 ' + (field as any).placeholder"
                    style="height: 30px"
                    @keydown.enter="filterSubmit"
                  />
                </template>

                <!-- 날짜 -->
                <template v-else-if="field.type === 'date'">
                  <DatePicker
                    v-if="cond[field.key] === 'is'"
                    v-model="form[field.key]"
                    :placeholder="field.label"
                    @update:model-value="filterSubmit"
                  />
                  <DatePicker
                    v-else-if="cond[field.key] === 'gte'"
                    v-model="form[`${field.key}__gte`]"
                    placeholder="이후"
                    @update:model-value="filterSubmit"
                  />
                  <DatePicker
                    v-else-if="cond[field.key] === 'lte'"
                    v-model="form[`${field.key}__lte`]"
                    placeholder="이전"
                    @update:model-value="filterSubmit"
                  />
                  <div v-else-if="cond[field.key] === 'between'" class="d-flex align-items-center">
                    <DatePicker
                      v-model="form[`${field.key}__between_min`]"
                      placeholder="시작"
                      @update:model-value="filterSubmit"
                    />
                    <span class="mx-1">~</span>
                    <DatePicker
                      v-model="form[`${field.key}__between_max`]"
                      placeholder="종료"
                      @update:model-value="filterSubmit"
                    />
                  </div>
                </template>

              </CCol>
            </CRow>
          </template>

        </CCol>

        <!-- 검색조건 추가 멀티셀렉트 -->
        <CCol md="4" class="text-right">
          <CRow>
            <CFormLabel
              for="calSearchOptions"
              class="col-4 col-lg-2 col-xl-4 col-xxl-5 col-form-label d-block d-md-none d-lg-block"
            >
              검색조건 추가
            </CFormLabel>
            <CCol class="col-8 col-md-12 col-lg-10 col-xl-8 col-xxl-7">
              <Multiselect
                mode="tags"
                v-model="searchCond"
                id="calSearchOptions"
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
    </CCollapse>
  </CRow>

  <!-- 검색 버튼 -->
  <CRow class="my-3">
    <CCol>
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
        v-if="can(PERM.PROJECT_SAVE_QUERY)"
        name="검색양식 저장"
        icon="mdi-content-save"
        icon-color="indigo"
        font-size="1"
        @click="openSaveModal"
      />
    </CCol>
  </CRow>

  <SaveQueryModal
    ref="refQuerySaveModal"
    :search-cond="searchCond"
    :target-type="targetType"
    :cond="cond"
    :form="form"
  />
</template>
