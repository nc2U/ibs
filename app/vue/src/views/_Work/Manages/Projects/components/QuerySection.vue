<script lang="ts" setup>
import { computed, onBeforeMount, onMounted, type PropType, reactive, ref, watch } from 'vue'
import { usePerms } from '@/composables/usePerms'
import { useInform } from '@/store/pinia/work_inform.ts'
import type { ProjectFilter, selectProject } from '@/store/types/work_project.ts'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import IssueProjectSelector from '@/views/_Work/components/atomics/IssueProjectSelector.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import SaveQueryModal from '@/views/_Work/components/SaveQueryModal.vue'

const props = defineProps({
  allReadableProjects: { type: Array as PropType<selectProject[]>, default: () => [] },
  targetType: {
    type: String as PropType<'project' | 'calendar' | 'issue' | 'meeting'>,
    default: 'project',
  },
})

const emit = defineEmits(['filter-submit', 'change-view-mode'])

const refQuerySaveModal = ref()

const { can, PERM } = usePerms()
const informStore = useInform()

const viewMode = ref<'board' | 'list'>(
  (localStorage.getItem('project-view-mode') as 'board' | 'list') || 'board',
)

watch(viewMode, nVal => {
  localStorage.setItem('project-view-mode', nVal)
  emit('change-view-mode', nVal)
})

const condVisible = ref(true)
const optVisible = ref(false)

const searchCond = ref(['status'])
const resetFilter = () => {
  searchCond.value = ['status']
  cond.value = {
    status: 'is',
    project: 'is',
    parent: 'all',
    is_public: 'is',
    created: 'is',
    updated: 'is',
    name: 'contains',
    description: 'contains',
  }
  form.value = {
    status: '1',
    is_public: '1',
    created_date: '',
    created_date2: '',
    updated_date: '',
    updated_date2: '',
    name: '',
    description: '',
    bookmark: undefined,
    my_project: undefined,
  }
  selectedProjectVal.value = ''
  if (props.allReadableProjects.length) {
    selectedParentVal.value = props.allReadableProjects[0]?.value
  }
  filterSubmit()
}

const searchOptions = reactive([
  {
    options: [
      { value: 'status', label: '상태' },
      { value: 'project', label: '프로젝트' },
      { value: 'parent', label: '상위 프로젝트' },
      { value: 'is_public', label: '공개여부' },
    ],
  },
  {
    label: '문자열 검색',
    options: [
      { value: 'name', label: '\u00A0\u00A0\u00A0이름' },
      { value: 'description', label: '\u00A0\u00A0\u00A0설명' },
    ],
  },
  {
    label: '날짜',
    options: [
      { value: 'created', label: '\u00A0\u00A0\u00A0등록일' },
      { value: 'updated', label: '\u00A0\u00A0\u00A0수정일' },
    ],
  },
])

const cond = ref<Record<string, any>>({
  status: 'is' as 'is' | 'exclude',
  project: 'is' as 'is' | 'exclude',
  parent: 'all' as 'all' | 'none' | 'is' | 'exclude',
  is_public: 'is' as 'is' | 'exclude',
  created: 'is' as 'is' | 'gte' | 'lte' | 'between',
  updated: 'is' as 'is' | 'gte' | 'lte' | 'between',

  name: 'contains',
  description: 'contains',
})

const form = ref<ProjectFilter & Record<string, any>>({
  status: '1',
  is_public: '1',

  created_date: '',
  created_date2: '',
  updated_date: '',
  updated_date2: '',

  name: '',
  description: '',

  bookmark: undefined,
  my_project: undefined,
})

const selectedProjectVal = ref<number | string>('')
const selectedParentVal = ref<number | string>('')

const filterFieldsConfig = computed(() => [
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
    key: 'parent',
    label: '상위 프로젝트',
    type: 'parent',
    condOptions: [
      { value: 'all', label: '모두' },
      { value: 'none', label: '없음' },
      { value: 'is', label: '이다' },
      { value: 'exclude', label: '아니다' },
    ],
  },
  {
    key: 'is_public',
    label: '공개여부',
    type: 'select',
    condOptions: [
      { value: 'is', label: '이다' },
      { value: 'exclude', label: '아니다' },
    ],
    options: [
      { value: '1', label: '예' },
      { value: '0', label: '아니오' },
    ],
  },
  {
    key: 'name',
    label: '이름',
    type: 'text-match',
    placeholder: '키워드 입력',
    condOptions: [
      { value: 'contains', label: '포함되는 키워드' },
      { value: 'exclude', label: '포함하지 않는 키워드' },
      { value: 'startswith', label: '앞문자 일치' },
      { value: 'endswith', label: '뒷문자 일치' },
      { value: 'none', label: '없음' },
      { value: 'any', label: '모두' },
    ],
  },
  {
    key: 'description',
    label: '설명',
    type: 'text-match',
    placeholder: '키워드 입력',
    condOptions: [
      { value: 'contains', label: '포함되는 키워드' },
      { value: 'exclude', label: '포함하지 않는 키워드' },
      { value: 'startswith', label: '앞문자 일치' },
      { value: 'endswith', label: '뒷문자 일치' },
      { value: 'none', label: '없음' },
      { value: 'any', label: '모두' },
    ],
  },
  {
    key: 'created',
    label: '등록일자',
    type: 'date',
    condOptions: [
      { value: 'is', label: '이다' },
      { value: 'gte', label: '>=' },
      { value: 'lte', label: '<=' },
      { value: 'between', label: '사이' },
    ],
  },
  {
    key: 'updated',
    label: '수정일자',
    type: 'date',
    condOptions: [
      { value: 'is', label: '이다' },
      { value: 'gte', label: '>=' },
      { value: 'lte', label: '<=' },
      { value: 'between', label: '사이' },
    ],
  },
])

const activeFields = computed(() => {
  return filterFieldsConfig.value.filter(field => searchCond.value.includes(field.key))
})

// ----- 활성화된 필터 키 관리 (체크박스로 ON/OFF 가능) -----
const enabledFields = ref<string[]>(['status'])

watch(searchCond, newVal => {
  newVal.forEach(key => {
    if (!enabledFields.value.includes(key)) {
      enabledFields.value.push(key)
    }
  })
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

const filterSubmit = () => {
  const filterData = {} as ProjectFilter & Record<string, any>

  if (enabledFields.value.includes('status')) {
    if (cond.value.status === 'is') filterData.status = form.value.status
    else if (cond.value.status === 'exclude') filterData.status__exclude = form.value.status
  }

  enabledFields.value.forEach(key => {
    if (key === 'status') return

    const operator = cond.value[key]
    const val = form.value[key]

    if (key === 'project') {
      if (selectedProjectVal.value === '') {
        if (operator === 'is') filterData.my_project = true
        else if (operator === 'exclude') filterData.my_project = false
      } else {
        delete filterData.status
        delete filterData.status__exclude
        const selectedProj = props.allReadableProjects.find(
          p => p.value === Number(selectedProjectVal.value),
        )
        const projectVal = selectedProj ? selectedProj.slug : String(selectedProjectVal.value)
        if (operator === 'is') filterData.project = projectVal
        else if (operator === 'exclude') filterData.project__exclude = projectVal
      }
    } else if (key === 'parent') {
      if (operator === 'all') {
        filterData.parent__isnull = false
      } else if (operator === 'none') {
        filterData.parent__isnull = true
      } else if (operator === 'is') {
        const selectedParent = props.allReadableProjects.find(
          p => p.value === Number(selectedParentVal.value),
        )
        filterData.parent = selectedParent ? selectedParent.slug : String(selectedParentVal.value)
      } else if (operator === 'exclude') {
        const selectedParent = props.allReadableProjects.find(
          p => p.value === Number(selectedParentVal.value),
        )
        filterData.parent__exclude = selectedParent
          ? selectedParent.slug
          : String(selectedParentVal.value)
      }
    } else if (key === 'is_public') {
      if (operator === 'is') filterData.is_public = form.value.is_public
      else if (operator === 'exclude') filterData.is_public__exclude = form.value.is_public
    } else if (key === 'name' || key === 'description') {
      if (operator === 'none') {
        filterData[`${key}__isnull`] = true
      } else if (operator === 'any') {
        filterData[`${key}__isnull`] = false
      } else if (val) {
        if (operator === 'contains') filterData[key] = val
        else if (operator === 'exclude') filterData[`${key}__exclude`] = val
        else if (operator === 'startswith') filterData[`${key}__startswith`] = val
        else if (operator === 'endswith') filterData[`${key}__endswith`] = val
      }
    } else if (key === 'created' || key === 'updated') {
      const fieldPrefix = key === 'created' ? 'created' : 'updated'
      const minVal = form.value[`${fieldPrefix}_date`]
      const maxVal = form.value[`${fieldPrefix}_date2`]
      const targetFrom = key === 'created' ? 'from_created' : 'from_updated'
      const targetTo = key === 'created' ? 'to_created' : 'to_updated'

      if (operator === 'is' && minVal) {
        filterData[targetFrom] = minVal
        filterData[targetTo] = minVal
      } else if (operator === 'gte' && minVal) {
        filterData[targetFrom] = minVal
      } else if (operator === 'lte' && minVal) {
        filterData[targetTo] = minVal
      } else if (operator === 'between' && minVal && maxVal) {
        filterData[targetFrom] = minVal
        filterData[targetTo] = maxVal
      }
    }
  })

  // 검색 양식 필터(bookmark, my_project)를 직접 필터데이터에 매핑
  if (form.value.bookmark !== undefined) filterData.bookmark = form.value.bookmark
  if (form.value.my_project !== undefined) filterData.my_project = form.value.my_project

  emit('filter-submit', filterData)
}

onBeforeMount(() => {
  selectedProjectVal.value = ''
  if (props.allReadableProjects.length) {
    selectedParentVal.value = props.allReadableProjects[0]?.value
  }
})

// 검색양식 관련 기능 구현
const myQueries = computed(() =>
  informStore.queries.filter(q => !q.is_public && q.target_type === props.targetType),
)
const publicQueries = computed(() =>
  informStore.queries.filter(q => q.is_public && q.target_type === props.targetType),
)

onMounted(() => {
  informStore.fetchQueries({ targetType: props.targetType })
})

const extraQueryData = computed(() => ({
  project: selectedProjectVal.value,
  parent: selectedParentVal.value,
}))

const openSaveModal = () => {
  refQuerySaveModal.value.callModal()
}

const applyQuery = (query: any) => {
  if (query && query.filters) {
    const f = query.filters

    // 이전 필터 상태 완전 초기화
    searchCond.value = ['status']
    enabledFields.value = ['status']
    cond.value = {
      status: 'is',
      project: 'is',
      parent: 'all',
      is_public: 'is',
      created: 'is',
      updated: 'is',
      name: 'contains',
      description: 'contains',
    }
    form.value = {
      status: '1',
      is_public: '1',
      created_date: '',
      created_date2: '',
      updated_date: '',
      updated_date2: '',
      name: '',
      description: '',
      bookmark: undefined,
      my_project: undefined,
    }
    selectedProjectVal.value = ''
    if (props.allReadableProjects.length) {
      selectedParentVal.value = props.allReadableProjects[0]?.value
    }

    if (f.searchCond) {
      searchCond.value = [...f.searchCond]
      enabledFields.value = [...f.searchCond]
    }
    if (f.cond) cond.value = { ...cond.value, ...f.cond }
    if (f.form) {
      form.value = { ...form.value, ...f.form }
      if (f.form.project !== undefined) selectedProjectVal.value = f.form.project
      if (f.form.parent !== undefined) selectedParentVal.value = f.form.parent
    } else {
      if (f.bookmark !== undefined) form.value.bookmark = f.bookmark
      if (f.my_project !== undefined) form.value.my_project = f.my_project
    }

    filterSubmit()
  }
}

const onQuerySelect = (event: Event) => {
  const select = event.target as HTMLSelectElement
  const queryId = Number(select.value)
  if (!queryId) return

  const query = informStore.queries.find(q => q.pk === queryId)
  if (query) {
    applyQuery(query)
  }
}

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
            <!-- 고정 필터: 상태 -->
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
                <CFormSelect v-model="cond.status" size="sm">
                  <option value="is">이다</option>
                  <option value="exclude">아니다</option>
                </CFormSelect>
              </CCol>
              <CCol v-if="enabledFields.includes('status')" class="col-8 col-lg-3">
                <CFormSelect v-model="form.status" size="sm">
                  <option value="1">사용중</option>
                  <option value="2">닫힘</option>
                </CFormSelect>
              </CCol>
            </CRow>

            <!-- 동적 검색조건 루프 -->
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
                  <template v-if="field.type === 'project'">
                    <IssueProjectSelector
                      v-model="selectedProjectVal"
                      :issue-project-list="allReadableProjects"
                      default-title="<< 내 프로젝트 >>"
                      size="sm"
                    />
                  </template>

                  <template v-else-if="field.type === 'parent'">
                    <IssueProjectSelector
                      v-if="cond.parent === 'is' || cond.parent === 'exclude'"
                      v-model="selectedParentVal"
                      :issue-project-list="allReadableProjects"
                      default-title="---------"
                      size="sm"
                    />
                  </template>

                  <template v-else-if="field.type === 'select'">
                    <CFormSelect v-model="form[field.key]" size="sm">
                      <option v-for="opt in field.options" :key="opt.value" :value="opt.value">
                        {{ opt.label }}
                      </option>
                    </CFormSelect>
                  </template>

                  <template v-else-if="field.type === 'text-match'">
                    <CFormInput
                      v-if="cond[field.key] !== 'none' && cond[field.key] !== 'any'"
                      v-model="form[field.key]"
                      :placeholder="field.placeholder"
                      size="sm"
                    />
                  </template>

                  <template v-else-if="field.type === 'date'">
                    <DatePicker v-model="form[`${field.key}_date`]" size="sm" />
                  </template>
                </CCol>

                <CCol
                  v-if="field.type === 'date' && cond[field.key] === 'between'"
                  class="col-4 col-lg-3"
                >
                  <DatePicker v-model="form[`${field.key}_date2`]" size="sm" />
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
              id="board-view-mode"
              value="board"
              inline
              type="radio"
            />
            <CFormCheck
              v-model="viewMode"
              label="목록"
              name="viewMode"
              id="list-view-mode"
              value="list"
              inline
              type="radio"
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
          v-if="can(PERM.PROJECT_SAVE_QUERY)"
          name="검색양식 저장"
          icon="mdi-content-save"
          icon-color="indigo"
          font-size="1"
          @click="openSaveModal"
        />

        <CFormSelect
          v-if="myQueries.length || publicQueries.length"
          class="d-inline-block ml-3"
          style="width: auto; max-width: 250px; vertical-align: middle"
          size="sm"
          @change="onQuerySelect"
        >
          <option value="">-- 검색양식 선택 --</option>
          <optgroup v-if="myQueries.length" label="내 검색양식">
            <option v-for="q in myQueries" :key="q.pk" :value="q.pk">
              {{ q.name }}
            </option>
          </optgroup>
          <optgroup v-if="publicQueries.length" label="공용 검색양식">
            <option v-for="q in publicQueries" :key="q.pk" :value="q.pk">
              {{ q.name }}
            </option>
          </optgroup>
        </CFormSelect>
      </slot>
    </CCol>
  </CRow>

  <SaveQueryModal
    ref="refQuerySaveModal"
    :search-cond="searchCond"
    :target-type="targetType"
    :cond="cond"
    :form="form"
    :extra-data="extraQueryData"
  />
</template>
