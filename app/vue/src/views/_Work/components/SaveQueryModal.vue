<script lang="ts" setup>
import { computed, ref, type PropType } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms'
import { useInform } from '@/store/pinia/work_inform.ts'
import type { selectProject } from '@/store/types/work_project.ts'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import IssueProjectSelector from '@/views/_Work/components/atomics/IssueProjectSelector.vue'
import FormModal from '@/components/Modals/FormModal.vue'

const props = defineProps({
  targetType: {
    type: String as PropType<'project' | 'calendar' | 'issue' | 'meeting'>,
    required: true,
  },
  searchCond: {
    type: Array as PropType<string[]>,
    required: true,
  },
  searchOptions: {
    type: Array as PropType<any[]>,
    required: true,
  },
  cond: {
    type: Object as PropType<Record<string, any>>,
    required: true,
  },
  form: {
    type: Object as PropType<Record<string, any>>,
    required: true,
  },
  activeFields: {
    type: Array as PropType<any[]>,
    default: () => [],
  },
  allReadableProjects: {
    type: Array as PropType<selectProject[]>,
    default: () => [],
  },
  extraData: {
    type: Object as PropType<Record<string, any>>,
    default: () => ({}),
  },
})

const emit = defineEmits<{
  (e: 'update:searchCond', val: string[]): void
  (e: 'saved'): void
}>()

const refModal = ref()
const { can, PERM } = usePerms()
const informStore = useInform()

const queryName = ref('')
const queryDescription = ref('')
const isPublic = ref(false)
const validated = ref(false)

const localSearchCond = computed({
  get: () => props.searchCond,
  set: (val: string[]) => emit('update:searchCond', val),
})

const callModal = () => {
  queryName.value = ''
  queryDescription.value = ''
  isPublic.value = false
  validated.value = false
  refModal.value.callModal()
}

const closeModal = () => {
  refModal.value.close()
}

const saveQuery = async (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
    return
  }
  validated.value = false

  const payload = {
    name: queryName.value,
    description: queryDescription.value,
    target_type: props.targetType,
    is_public: isPublic.value,
    project: props.extraData.project || null,
    filters: {
      searchCond: props.searchCond,
      cond: props.cond,
      form: {
        ...props.form,
        ...props.extraData,
      },
    },
  }

  await informStore.createQuery(payload)
  await informStore.fetchQueries({ targetType: props.targetType })
  closeModal()
  emit('saved')
}

defineExpose({ callModal, closeModal })
</script>

<template>
  <FormModal ref="refModal" size="lg">
    <template #header>검색양식 저장</template>
    <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="saveQuery">
      <CModalBody class="text-body">
        <CRow class="mb-3">
          <CFormLabel for="query-name" class="col-3 col-form-label required text-right">
            이름
          </CFormLabel>
          <CCol class="col-7">
            <CFormInput id="query-name" v-model="queryName" placeholder="검색양식 이름" required />
          </CCol>
        </CRow>
        <CRow class="mb-3">
          <CFormLabel for="query-desc" class="col-3 col-form-label text-right"> 설명 </CFormLabel>
          <CCol class="col-7">
            <CFormInput id="query-desc" v-model="queryDescription" placeholder="검색양식 설명" />
          </CCol>
        </CRow>
        <CRow class="mb-3" v-if="can(PERM.PROJECT_PUB_QUERY)">
          <CCol class="offset-3 col-7">
            <CFormCheck id="query-is-public" v-model="isPublic" label="공용 (공유)" />
          </CCol>
        </CRow>
        <CRow class="mb-3">
          <CFormLabel for="modalSearchOptions" class="col-3 col-form-label text-right">
            검색 조건 추가
          </CFormLabel>
          <CCol class="col-7 pt-1">
            <Multiselect
              id="modalSearchOptions"
              v-model="localSearchCond"
              mode="tags"
              placeholder="검색조건 추가"
              :options="searchOptions"
              :groups="true"
              :close-on-select="false"
              :searchable="false"
              :create-option="false"
              size="sm"
            />
          </CCol>
        </CRow>

        <v-divider class="my-4" />
        <h6 class="mb-3 text-indigo">
          <v-icon icon="mdi-filter-cog" class="mr-2" size="small" />
          저장될 검색 조건 설정
        </h6>

        <div class="px-3 py-2 border rounded bg-light">
          <!-- 상태 (상태 필드가 cond에 존재하는 경우) -->
          <CRow v-if="'status' in cond" class="mb-2 align-items-center">
            <CCol class="col-3 pt-1 text-right">
              <strong>상태</strong>
            </CCol>
            <CCol class="col-3">
              <CFormSelect v-model="cond.status" size="sm">
                <option value="is">이다</option>
                <option value="exclude">아니다</option>
              </CFormSelect>
            </CCol>
            <CCol class="col-4">
              <CFormSelect v-model="form.status" size="sm">
                <option value="1">사용중</option>
                <option value="2">닫힘</option>
              </CFormSelect>
            </CCol>
          </CRow>

          <!-- 저장 조건 설정용 동적 검색조건 루프 -->
          <template v-for="field in activeFields" :key="'modal-' + field.key">
            <CRow class="mb-2 align-items-center">
              <CCol class="col-3 pt-1 text-right">
                <strong>{{ field.label }}</strong>
              </CCol>
              <CCol class="col-3">
                <CFormSelect v-model="cond[field.key]" size="sm">
                  <option v-for="opt in field.condOptions" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </option>
                </CFormSelect>
              </CCol>
              <CCol class="col-4">
                <!-- 프로젝트 전용 셀렉트 -->
                <template v-if="field.type === 'project'">
                  <IssueProjectSelector
                    v-model="extraData.selectedProjectVal"
                    :issue-project-list="allReadableProjects"
                    default-title="<< 내 프로젝트 >>"
                    size="sm"
                  />
                </template>

                <!-- 상위 프로젝트 셀렉트 -->
                <template v-else-if="field.type === 'parent'">
                  <IssueProjectSelector
                    v-if="cond.parent === 'is' || cond.parent === 'exclude'"
                    v-model="extraData.selectedParentVal"
                    :issue-project-list="allReadableProjects"
                    default-title="---------"
                    size="sm"
                  />
                </template>

                <!-- 일반 단일 셀렉트 -->
                <template v-else-if="field.type === 'select'">
                  <CFormSelect v-model="form[field.key]" size="sm">
                    <option v-for="opt in field.options" :key="opt.value" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </CFormSelect>
                </template>

                <!-- 멀티 셀렉트 (담당자, 작성자, 참석자 등) -->
                <template v-else-if="field.type === 'multiselect'">
                  <Multiselect
                    v-model="form[field.key]"
                    :options="field.options"
                    :placeholder="field.placeholder || '선택'"
                    size="sm"
                  />
                </template>

                <!-- 문자열 텍스트 일치 검색 -->
                <template v-else-if="field.type === 'text-match' || field.type === 'text'">
                  <CFormInput
                    v-if="cond[field.key] !== 'none' && cond[field.key] !== 'any'"
                    v-model="form[field.key]"
                    :placeholder="field.placeholder || '검색어 입력'"
                    size="sm"
                  />
                </template>

                <!-- 단일 날짜 입력 -->
                <template v-else-if="field.type === 'date'">
                  <DatePicker v-model="form[`${field.key}_date`]" size="sm" />
                </template>
              </CCol>

              <!-- 범주 날짜 보조 입력 -->
              <CCol v-if="field.type === 'date' && cond[field.key] === 'between'" class="col-3">
                <DatePicker v-model="form[`${field.key}_date2`]" size="sm" />
              </CCol>
            </CRow>
          </template>
        </div>
      </CModalBody>
      <CModalFooter>
        <v-btn type="submit" size="small" color="indigo" class="text-white">저장</v-btn>
        <v-btn color="light" size="small" @click="closeModal" flat>닫기</v-btn>
      </CModalFooter>
    </CForm>
  </FormModal>
</template>
