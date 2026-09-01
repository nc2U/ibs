<script lang="ts" setup>
import { computed, onMounted, type PropType, reactive, ref, watch } from 'vue'
import { usePerms } from '@/composables/usePerms'
import type { selectProject } from '@/store/types/work_project.ts'
import type { IssueStatus, Tracker } from '@/store/types/work_issue.ts'
import type { MeetingCategory } from '@/store/types/work_meeting.ts'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import IssueProjectSelector from '@/views/_Work/components/atomics/IssueProjectSelector.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import SaveQueryModal from '@/views/_Work/components/SaveQueryModal.vue'

import { useRoute } from 'vue-router'
import { useAccount } from '@/store/pinia/account'

import { storeToRefs } from 'pinia'
import { useCalendarFilter } from '@/store/pinia/work_calendar_filter.ts'

const route = useRoute()
const { can, PERM } = usePerms()
const accStore = useAccount()
const currentUserId = computed(() => accStore.userInfo?.pk)

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

const calendarFilterStore = useCalendarFilter()
const { eventTypes, searchCond, enabledFields, cond, form } = storeToRefs(calendarFilterStore)

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

// searchCond 에 새 항목 추가 시 enabledFields 에도 자동 추가
watch(searchCond, newVal => {
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
  const payload = calendarFilterStore.buildFilterPayload()
  emit('filter-submit', payload)
}

// ----- 초기화 -----
const resetFilter = () => {
  const payload = calendarFilterStore.resetFilter()
  emit('filter-submit', payload)
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

// ----- 저장된 검색양식 복원 (Apply Query) -----
const applyQuery = (query: any) => {
  const payload = calendarFilterStore.applySavedQuery(
    query,
    currentUserId.value,
    props.getUsers[0]?.value,
  )
  if (payload) {
    emit('filter-submit', payload)
  }
}

onMounted(() => filterSubmit())

defineExpose({ applyQuery, resetFilter })
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
              <CFormCheck id="evt-issue" v-model="eventTypes" value="issue" label="업무" inline />
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
                    show-book-mark-option
                    show-closed-option
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
                    <option
                      v-for="opt in (field as any).options"
                      :key="opt.value"
                      :value="opt.value"
                    >
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
