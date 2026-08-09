<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import { useAccount } from '@/store/pinia/account'
import { useInform } from '@/store/pinia/work_inform'
import type { selectProject } from '@/store/types/work_project.ts'
import type { MeetingCategory, MeetingFilter } from '@/store/types/work_meeting.ts'
import IssueProjectSelector from '@/views/_Work/components/atomics/IssueProjectSelector.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import Multiselect from '@vueform/multiselect'

const props = defineProps({
  categories: { type: Array as PropType<MeetingCategory[]>, default: () => [] },
  searchProjects: { type: Array as PropType<selectProject[]>, default: () => [] },
  targetType: {
    type: String as PropType<'project' | 'calendar' | 'issue' | 'meeting'>,
    default: 'meeting',
  },
})

const emit = defineEmits<{
  (e: 'filter-submit', payload: MeetingFilter): void
}>()

const viewMode = ref<'board' | 'list'>('board')
const condVisible = ref(true)
const optVisible = ref(false)

const route = useRoute()
const accStore = useAccount()
const getUsers = computed(() => accStore.getUsers)

const informStore = useInform()
const { can, PERM } = usePerms()

// 개인 및 공용 검색양식 저장 권한 확인
const canSaveQuery = computed(() => can(PERM.PROJECT_SAVE_QUERY))
const canPubQuery = computed(() => can(PERM.PROJECT_PUB_QUERY))
const canAnySaveQuery = computed(() => canSaveQuery.value || canPubQuery.value)

const searchCond = ref<string[]>(['status'])

const refQuerySaveModal = ref()
const queryForm = reactive({
  name: '',
  description: '',
  is_public: false,
})

const openSaveQueryModal = () => {
  queryForm.name = ''
  queryForm.description = ''
  // 공용 권한만 있는 경우 기본값을 true로 설정
  queryForm.is_public = canPubQuery.value && !canSaveQuery.value
  refQuerySaveModal.value.callModal()
}

const saveQuery = async () => {
  if (!queryForm.name.trim()) return

  const projId = (route.params.projId as string) || ''
  const projectObj = props.searchProjects.find(p => p.slug === projId)

  const payload = {
    name: queryForm.name,
    description: queryForm.description,
    target_type: props.targetType,
    project: projectObj ? projectObj.value : null,
    is_public: queryForm.is_public,
    filters: {
      searchCond: searchCond.value,
      cond: { ...cond },
      form: { ...form },
    },
  }

  await informStore.createQuery(payload)
  await informStore.fetchQueries({ targetType: props.targetType })
  refQuerySaveModal.value.close()
}

const applyQuery = (query: any) => {
  if (query && query.filters) {
    const f = query.filters
    if (f.searchCond) searchCond.value = f.searchCond
    if (f.cond) Object.assign(cond, f.cond)
    if (f.form) Object.assign(form, f.form)
    filterSubmit()
  }
}

const resetFilter = () => {
  searchCond.value = ['status']
  form.status = '1'
  form.is_confirmed = ''
  form.category = undefined
  form.creator = null
  form.attendees = null
  form.meeting_date_after = ''
  form.meeting_date_before = ''
  form.created_after = ''
  form.created_before = ''
  form.title = ''
  form.agenda = ''
  form.content = ''
  form.decisions = ''

  cond.status = 'open'
  cond.is_confirmed = 'is'
  cond.category = 'is'
  cond.creator = 'is'
  cond.attendees = 'is'
  cond.meeting_date = 'between'
  cond.created = 'between'
  cond.title = 'contains'
  cond.agenda = 'contains'
  cond.content = 'contains'
  cond.decisions = 'contains'

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
}

const searchOptions = reactive<SearchOptionGroup[]>([
  {
    options: [
      { value: 'status', label: '상태', disabled: true },
      { value: 'is_confirmed', label: '확정 여부' },
      { value: 'category', label: '카테고리' },
      { value: 'creator', label: '작성자' },
      { value: 'attendees', label: '참석자' },
    ],
  },
  {
    label: '문자열 검색',
    options: [
      { value: 'title', label: '\u00A0\u00A0\u00A0제목' },
      { value: 'agenda', label: '\u00A0\u00A0\u00A0의제' },
      { value: 'content', label: '\u00A0\u00A0\u00A0내용' },
      { value: 'decisions', label: '\u00A0\u00A0\u00A0결정사항' },
    ],
  },
  {
    label: '날짜별 검색',
    options: [
      { value: 'meeting_date', label: '\u00A0\u00A0\u00A0회의 일시' },
      { value: 'created', label: '\u00A0\u00A0\u00A0등록일' },
    ],
  },
])

const cond = reactive<Record<string, string>>({
  status: 'open',
  project: 'is',
  is_confirmed: 'is',
  category: 'is',
  creator: 'is',
  attendees: 'is',
  meeting_date: 'between',
  created: 'between',
  title: 'contains',
  agenda: 'contains',
  content: 'contains',
  decisions: 'contains',
})

const form = reactive<any>({
  project: (route.params.projId as string) ?? '',
  status: '1',
  is_confirmed: '',
  category: undefined,
  creator: null,
  attendees: null,
  meeting_date_after: '',
  meeting_date_before: '',
  created_after: '',
  created_before: '',
  title: '',
  agenda: '',
  content: '',
  decisions: '',
})

// 동적 필드 정보 계산
const activeFields = computed(() => {
  const fields: any[] = []

  if (searchCond.value.includes('project') && !route.params.projId) {
    fields.push({
      key: 'project',
      label: '프로젝트',
      type: 'project',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
    })
  }

  if (searchCond.value.includes('is_confirmed')) {
    fields.push({
      key: 'is_confirmed',
      label: '확정 여부',
      type: 'select',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
      options: [
        { value: 'true', label: '확정됨' },
        { value: 'false', label: '미확정' },
      ],
    })
  }

  if (searchCond.value.includes('category')) {
    fields.push({
      key: 'category',
      label: '카테고리',
      type: 'select',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
      options: props.categories.map(c => ({ value: c.pk, label: c.name })),
    })
  }

  if (searchCond.value.includes('creator')) {
    fields.push({
      key: 'creator',
      label: '작성자',
      type: 'select',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
      options: getUsers.value,
    })
  }

  if (searchCond.value.includes('attendees')) {
    fields.push({
      key: 'attendees',
      label: '참석자',
      type: 'select',
      condOptions: [
        { value: 'is', label: '이다' },
        { value: 'exclude', label: '아니다' },
      ],
      options: getUsers.value,
    })
  }

  if (searchCond.value.includes('meeting_date')) {
    fields.push({
      key: 'meeting_date',
      label: '회의 일시',
      type: 'date',
      condOptions: [
        { value: 'between', label: '범위' },
        { value: 'gte', label: '이후' },
        { value: 'lte', label: '이전' },
      ],
    })
  }

  if (searchCond.value.includes('created')) {
    fields.push({
      key: 'created',
      label: '등록일',
      type: 'date',
      condOptions: [
        { value: 'between', label: '범위' },
        { value: 'gte', label: '이후' },
        { value: 'lte', label: '이전' },
      ],
    })
  }

  const stringFields = ['title', 'agenda', 'content', 'decisions']
  const stringLabels: Record<string, string> = {
    title: '제목',
    agenda: '의제',
    content: '내용',
    decisions: '결정사항',
  }

  stringFields.forEach(f => {
    if (searchCond.value.includes(f)) {
      fields.push({
        key: f,
        label: stringLabels[f],
        type: 'text',
        condOptions: [
          { value: 'contains', label: '포함' },
          { value: 'exclude', label: '미포함' },
        ],
      })
    }
  })

  return fields
})

const filterSubmit = () => {
  const payload: MeetingFilter = { page: 1 }

  if (route.params.projId) {
    payload.project = route.params.projId as string
  } else if (searchCond.value.includes('project') && form.project) {
    payload.project = form.project
  }

  // 상태 처리
  if (cond.status === 'open') {
    payload.status = '1' // 준비중
  } else if (cond.status === 'closed') {
    payload.status = '2' // 완료됨
  } else if (cond.status === 'is') {
    payload.status = form.status
  } else if (cond.status === 'any') {
    delete payload.status
  }

  // 확정 여부
  if (searchCond.value.includes('is_confirmed')) {
    if (cond.is_confirmed === 'is') {
      payload.is_confirmed = form.is_confirmed === 'true'
    }
  }

  // 카테고리
  if (searchCond.value.includes('category') && form.category) {
    payload.category = form.category
  }

  // 작성자
  if (searchCond.value.includes('creator') && form.creator) {
    payload.creator = form.creator
  }

  // 참석자
  if (searchCond.value.includes('attendees') && form.attendees) {
    payload.attendees = form.attendees
  }

  // 회의 일시 범위
  if (searchCond.value.includes('meeting_date')) {
    if (cond.meeting_date === 'between') {
      if (form.meeting_date_after) payload.meeting_date_after = form.meeting_date_after
      if (form.meeting_date_before) payload.meeting_date_before = form.meeting_date_before
    } else if (cond.meeting_date === 'gte' && form.meeting_date_after) {
      payload.meeting_date_after = form.meeting_date_after
    } else if (cond.meeting_date === 'lte' && form.meeting_date_before) {
      payload.meeting_date_before = form.meeting_date_before
    }
  }

  // 등록일 범위
  if (searchCond.value.includes('created')) {
    if (cond.created === 'between') {
      if (form.created_after) payload.created_after = form.created_after
      if (form.created_before) payload.created_before = form.created_before
    } else if (cond.created === 'gte' && form.created_after) {
      payload.created_after = form.created_after
    } else if (cond.created === 'lte' && form.created_before) {
      payload.created_before = form.created_before
    }
  }

  // 문자열 검색
  const searchTerms: string[] = []
  if (searchCond.value.includes('title') && form.title) searchTerms.push(form.title)
  if (searchCond.value.includes('agenda') && form.agenda) searchTerms.push(form.agenda)
  if (searchCond.value.includes('content') && form.content) searchTerms.push(form.content)
  if (searchCond.value.includes('decisions') && form.decisions) searchTerms.push(form.decisions)

  if (searchTerms.length) {
    payload.search = searchTerms.join(' ')
  }

  emit('filter-submit', payload)
}

watch(
  () => searchCond.value,
  nVal => {
    if (nVal.includes('category') && !form.category && props.categories.length) {
      form.category = props.categories[0].pk
    }
    if (nVal.includes('creator') && !form.creator && getUsers.value.length) {
      form.creator = getUsers.value[0].value
    }
    if (nVal.includes('attendees') && !form.attendees && getUsers.value.length) {
      form.attendees = getUsers.value[0].value
    }
  },
  { deep: true },
)

onBeforeMount(() => {
  if (!route.params.projId) {
    searchOptions[0].options.splice(1, 0, { value: 'project', label: '프로젝트' })
  }
})

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
      <slot name="condition">
        <CRow class="m-2" color="light">
          <CCol class="col-12 col-md-8">
            <!-- 1. 고정 필터: 상태 -->
            <CRow>
              <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                <CFormCheck label="상태" id="status" checked readonly />
              </CCol>
              <CCol class="d-none d-lg-block col-4 col-lg-3 col-xl-2">
                <CFormSelect v-model="cond.status" size="sm">
                  <option value="open">준비중</option>
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
                  <option value="1">준비중</option>
                  <option value="2">완료됨</option>
                  <option value="3">취소됨</option>
                </CFormSelect>
              </CCol>
            </CRow>

            <!-- 2. 동적 추가 필터 리스트 -->
            <template v-for="field in activeFields" :key="field.key">
              <CRow>
                <!-- 라벨 & 체크박스 -->
                <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                  <CFormCheck checked readonly :label="field.label" :id="field.key" />
                </CCol>

                <!-- 연산자 조건 선택기 -->
                <CCol class="col-4 col-lg-3 col-xl-2">
                  <CFormSelect v-model="cond[field.key]" size="sm">
                    <option v-for="opt in field.condOptions" :key="opt.value" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </CFormSelect>
                </CCol>

                <!-- 실제 입력 필드 렌더링부 -->
                <CCol class="col-4 col-lg-3">
                  <!-- 프로젝트 전용 셀렉트 -->
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
                      <option v-for="opt in field.options" :key="opt.value" :value="opt.value">
                        {{ opt.label }}
                      </option>
                    </CFormSelect>
                  </template>

                  <!-- 문자열 검색 텍스트 필드 -->
                  <template v-else-if="field.type === 'text'">
                    <CFormInput
                      v-model="form[field.key]"
                      size="sm"
                      placeholder="검색어 입력"
                      @keyup.enter="filterSubmit"
                    />
                  </template>

                  <!-- 날짜 입력 필드 (DatePicker) -->
                  <template v-else-if="field.type === 'date'">
                    <template v-if="cond[field.key] === 'between'">
                      <DatePicker
                        v-model="form[`${field.key}_after`]"
                        placeholder="시작일"
                        size="sm"
                      />
                      <span class="mx-1">~</span>
                      <DatePicker
                        v-model="form[`${field.key}_before`]"
                        placeholder="종료일"
                        size="sm"
                      />
                    </template>
                    <template v-else-if="cond[field.key] === 'gte'">
                      <DatePicker
                        v-model="form[`${field.key}_after`]"
                        placeholder="시작일"
                        size="sm"
                      />
                    </template>
                    <template v-else-if="cond[field.key] === 'lte'">
                      <DatePicker
                        v-model="form[`${field.key}_before`]"
                        placeholder="종료일"
                        size="sm"
                      />
                    </template>
                  </template>
                </CCol>
              </CRow>
            </template>
          </CCol>

          <!-- 오른쪽 검색 항목 추가 멀티셀렉트 -->
          <CCol class="col-12 col-md-4">
            <CRow>
              <CCol class="col-4 col-sm-3 col-md-5 col-lg-4 col-xl-3 pt-1">
                <CFormLabel for="add_filter" class="col-form-label">검색 항목 추가</CFormLabel>
              </CCol>
              <CCol class="col-8 col-sm-9 col-md-7 col-lg-8 col-xl-9">
                <Multiselect
                  v-model="searchCond"
                  :options="searchOptions"
                  mode="tags"
                  :groups="true"
                  placeholder="검색 항목 추가..."
                  size="sm"
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

  <!-- 버튼 영역 -->
  <CRow class="my-3">
    <CCol>
      <slot name="footer">
        <TextButton name="적용" icon="mdi-magnify" icon-color="info" @click="filterSubmit" />

        <TextButton
          name="초기화"
          icon="mdi-autorenew"
          icon-color="info"
          font-size="1"
          @click="resetFilter"
        />

        <TextButton
          v-if="canAnySaveQuery"
          name="검색양식 저장"
          icon="mdi-content-save"
          icon-color="indigo"
          font-size="1"
          @click="openSaveQueryModal"
        />
      </slot>
    </CCol>
  </CRow>

  <!-- 검색 양식 저장 모달 -->
  <FormModal ref="refQuerySaveModal" title="검색 양식 저장" size="lg">
    <template #default>
      <CRow class="mb-3">
        <CFormLabel for="query-name" class="col-sm-3 col-form-label">이름 *</CFormLabel>
        <CCol class="col-sm-9">
          <CFormInput
            id="query-name"
            v-model="queryForm.name"
            placeholder="검색 양식 이름을 입력하세요"
            required
          />
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="query-desc" class="col-sm-3 col-form-label">설명</CFormLabel>
        <CCol class="col-sm-9">
          <CFormInput
            id="query-desc"
            v-model="queryForm.description"
            placeholder="양식에 대한 간단한 설명을 입력하세요"
          />
        </CCol>
      </CRow>

      <!-- 저장 대상 권한 옵션 -->
      <CRow class="mb-3">
        <CFormLabel class="col-sm-3 col-form-label">공유 설정</CFormLabel>
        <CCol class="col-sm-9 pt-1">
          <!-- 개인 및 공용 모두 가능한 경우 -->
          <template v-if="canSaveQuery && canPubQuery">
            <CFormCheck
              id="query-public"
              v-model="queryForm.is_public"
              label="공용 (모든 사용자와 공유)"
            />
            <div class="form-text text-muted">
              체크하지 않으면 내 개인 검색 양식으로만 저장됩니다.
            </div>
          </template>

          <!-- 개인 저장 권한만 있는 경우 -->
          <template v-else-if="canSaveQuery && !canPubQuery">
            <CFormCheck
              id="query-public-disabled"
              :checked="false"
              disabled
              label="개인 전용 저장 (공용 저장 권한 없음)"
            />
            <div class="form-text text-muted">개인 검색 양식으로 저장됩니다.</div>
          </template>

          <!-- 공용 저장 권한만 있는 경우 -->
          <template v-else-if="!canSaveQuery && canPubQuery">
            <CFormCheck
              id="query-public-forced"
              :checked="true"
              disabled
              label="공용 (모든 사용자와 공유)"
            />
            <div class="form-text text-muted">공용 검색 양식으로 저장됩니다.</div>
          </template>
        </CCol>
      </CRow>
    </template>

    <template #footer>
      <v-btn color="primary" size="small" @click="saveQuery">저장</v-btn>
      <v-btn color="light" size="small" variant="text" @click="refQuerySaveModal.close()" flat>
        취소
      </v-btn>
    </template>
  </FormModal>
</template>

<style scoped>
:deep(.multiselect) {
  min-height: 31px !important;
  font-size: 0.875rem;
}
</style>
