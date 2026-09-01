<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, reactive, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import { useAccount } from '@/store/pinia/account'
import { useMeetingFilter } from '@/store/pinia/work_meeting_filter.ts'
import type { selectProject } from '@/store/types/work_project.ts'
import type { MeetingCategory, MeetingFilter } from '@/store/types/work_meeting.ts'
import IssueProjectSelector from '@/views/_Work/components/atomics/IssueProjectSelector.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import SaveQueryModal from '@/views/_Work/components/SaveQueryModal.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
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

const condVisible = ref(true)
const optVisible = ref(false)

const route = useRoute()
const accStore = useAccount()
const getUsers = computed(() => accStore.getUsers)

const { can, PERM } = usePerms()
const canSaveQuery = computed(() => can(PERM.PROJECT_SAVE_QUERY))

const meetingFilterStore = useMeetingFilter()
const { searchCond, enabledFields, cond, form } = storeToRefs(meetingFilterStore)

const refQuerySaveModal = ref()

const extraQueryData = computed(() => {
  const projId = (route.params.projId as string) || ''
  const projectObj = props.searchProjects.find(p => p.slug === projId)
  return { project: projectObj ? projectObj.value : null }
})

const openSaveQueryModal = () => {
  refQuerySaveModal.value.callModal()
}

const currentUserId = computed(() => accStore.userInfo?.pk)

const applyQuery = (query: any) => {
  const currentProjSlug = (route.params.projId as string) || ''
  const payload = meetingFilterStore.applySavedQuery(
    query,
    currentUserId.value,
    getUsers.value[0]?.value,
    currentProjSlug,
  )
  if (payload) {
    emit('filter-submit', payload)
  }
}

const resetFilter = () => {
  const currentProjSlug = (route.params.projId as string) || ''
  const payload = meetingFilterStore.resetFilter(currentProjSlug)
  emit('filter-submit', payload)
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
      { value: 'status', label: '상태' },
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

const toggleField = (key: string, e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.checked) {
    if (!enabledFields.value.includes(key)) enabledFields.value.push(key)
  } else {
    enabledFields.value = enabledFields.value.filter(k => k !== key)
  }
  filterSubmit()
}

const filterSubmit = () => {
  const currentProjSlug = (route.params.projId as string) || ''
  const payload = meetingFilterStore.buildFilterPayload(currentProjSlug)
  emit('filter-submit', payload)
}

watch(
  () => searchCond.value,
  newVal => {
    newVal.forEach(key => {
      if (!enabledFields.value.includes(key)) {
        enabledFields.value.push(key)
      }
    })
    enabledFields.value = enabledFields.value.filter(k => newVal.includes(k))

    if (newVal.includes('is_confirmed') && !form.value.is_confirmed) {
      form.value.is_confirmed = 'true'
    }
    if (newVal.includes('category') && !form.value.category && props.categories.length) {
      form.value.category = props.categories[0].pk
    }
    if (newVal.includes('creator') && !form.value.creator && getUsers.value.length) {
      form.value.creator = currentUserId.value ?? getUsers.value[0].value
    }
    if (newVal.includes('attendees') && !form.value.attendees && getUsers.value.length) {
      form.value.attendees = currentUserId.value ?? getUsers.value[0].value
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
                <CFormCheck
                  label="상태"
                  id="status"
                  :checked="enabledFields.includes('status')"
                  @change="toggleField('status', $event)"
                />
              </CCol>
              <CCol
                v-if="enabledFields.includes('status')"
                class="d-none d-lg-block col-4 col-lg-3 col-xl-2"
              >
                <CFormSelect v-model="cond.status" size="sm" @change="filterSubmit">
                  <option value="open">준비중</option>
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                  <option value="closed">종료됨</option>
                  <option value="any">모두</option>
                </CFormSelect>
              </CCol>
              <CCol v-if="enabledFields.includes('status')" class="col-8 col-lg-3">
                <CFormSelect
                  v-if="cond.status === 'is' || cond.status === 'exclude'"
                  v-model="form.status"
                  size="sm"
                  @change="filterSubmit"
                >
                  <option value="1">준비</option>
                  <option value="2">종료</option>
                  <option value="3">취소</option>
                </CFormSelect>
              </CCol>
            </CRow>

            <!-- 2. 동적 추가 필터 리스트 -->
            <template v-for="field in activeFields" :key="field.key">
              <CRow>
                <!-- 라벨 & 체크박스 -->
                <CCol class="col-4 col-lg-3 col-xl-2 pt-1 mb-3">
                  <CFormCheck
                    :label="field.label"
                    :id="field.key"
                    :checked="enabledFields.includes(field.key)"
                    @change="toggleField(field.key, $event)"
                  />
                </CCol>

                <!-- 연산자 조건 선택기 -->
                <CCol v-if="enabledFields.includes(field.key)" class="col-4 col-lg-3 col-xl-2">
                  <CFormSelect v-model="cond[field.key]" size="sm" @change="filterSubmit">
                    <option v-for="opt in field.condOptions" :key="opt.value" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </CFormSelect>
                </CCol>

                <!-- 실제 입력 필드 렌더링부 -->
                <CCol v-if="enabledFields.includes(field.key)" class="col-4 col-lg-3">
                  <!-- 프로젝트 전용 셀렉트 -->
                  <template v-if="field.type === 'project'">
                    <IssueProjectSelector
                      v-model="form.project"
                      :issue-project-list="searchProjects"
                      default-title="<< 내 워크스페이스 >>"
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
                      @change="filterSubmit"
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
      <slot name="option"> </slot>
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
          v-if="canSaveQuery"
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
  <SaveQueryModal
    ref="refQuerySaveModal"
    :search-cond="searchCond"
    :target-type="targetType"
    :cond="cond"
    :form="form"
    :extra-data="extraQueryData"
  />
</template>

<style scoped>
:deep(.multiselect) {
  min-height: 31px !important;
  font-size: 0.875rem;
}
</style>
