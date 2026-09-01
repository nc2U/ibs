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

import { storeToRefs } from 'pinia'
import { useProjectFilter } from '@/store/pinia/work_project_filter.ts'

const props = defineProps({
  allReadableProjects: { type: Array as PropType<selectProject[]>, default: () => [] },
  targetType: {
    type: String as PropType<'project' | 'calendar' | 'issue' | 'meeting'>,
    default: 'project',
  },
  showLockedOption: { type: Boolean, default: false },
})

const emit = defineEmits(['filter-submit', 'change-view-mode'])

const refQuerySaveModal = ref()

const { can, PERM } = usePerms()
const informStore = useInform()

const projectFilterStore = useProjectFilter()
const { searchCond, enabledFields, cond, form, selectedProjectVal, selectedParentVal } =
  storeToRefs(projectFilterStore)

const condVisible = ref(true)
const optVisible = ref(false)

const resetFilter = () => {
  const payload = projectFilterStore.resetFilter(props.allReadableProjects)
  emit('filter-submit', payload)
}

const searchOptions = reactive([
  {
    options: [
      { value: 'status', label: '상태' },
      { value: 'project', label: '워크스페이스' },
      { value: 'parent', label: '상위 워크스페이스' },
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

const filterFieldsConfig = computed(() => [
  {
    key: 'project',
    label: '워크스페이스',
    type: 'project',
    condOptions: [
      { value: 'is', label: '이다' },
      { value: 'exclude', label: '아니다' },
    ],
  },
  {
    key: 'parent',
    label: '상위 워크스페이스',
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
  const filterData = projectFilterStore.buildFilterPayload(props.allReadableProjects)
  emit('filter-submit', filterData)
}

onBeforeMount(() => {
  if (selectedProjectVal.value === undefined) selectedProjectVal.value = ''
  if (!selectedParentVal.value && props.allReadableProjects.length) {
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
  const payload = projectFilterStore.applySavedQuery(query, props.allReadableProjects)
  if (payload) {
    emit('filter-submit', payload)
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
                  <option v-if="showLockedOption" value="9">잠금보관</option>
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
                      default-title="<< 내 워크스페이스 >>"
                      show-book-mark-option
                      show-closed-option
                      size="sm"
                    />
                  </template>

                  <template v-else-if="field.type === 'parent'">
                    <IssueProjectSelector
                      v-if="cond.parent === 'is' || cond.parent === 'exclude'"
                      v-model="selectedParentVal"
                      :issue-project-list="allReadableProjects"
                      default-title="---------"
                      show-book-mark-option
                      show-closed-option
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
      <slot name="option"> </slot>
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
