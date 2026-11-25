<script lang="ts" setup>
import { ref, type PropType } from 'vue'
import { isValidate } from '@/utils/helper'
import { usePerms } from '@/composables/usePerms'
import { useInform } from '@/store/pinia/work_inform'
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
  cond: {
    type: Object as PropType<Record<string, unknown>>,
    required: true,
  },
  form: {
    type: Object as PropType<Record<string, unknown>>,
    required: true,
  },
  extraData: {
    type: Object as PropType<Record<string, unknown>>,
    default: () => ({}),
  },
  extraFilters: {
    type: Object as PropType<Record<string, unknown>>,
    default: () => ({}),
  },
  projectId: {
    type: Number as PropType<number | null>,
    default: null,
  },
})

const emit = defineEmits<{
  (e: 'saved'): void
}>()

const refModal = ref<InstanceType<typeof FormModal> | null>(null)
const { can, PERM } = usePerms()
const informStore = useInform()

const queryName = ref('')
const queryDescription = ref('')
const isPublic = ref(false)
const validated = ref(false)
const submitting = ref(false)

const callModal = () => {
  queryName.value = ''
  queryDescription.value = ''
  isPublic.value = false
  validated.value = false
  submitting.value = false
  refModal.value?.callModal()
}

const closeModal = () => {
  refModal.value?.close()
}

const saveQuery = async (event: Event) => {
  if (submitting.value) return
  queryName.value = queryName.value.trim()
  if (isValidate(event) || !queryName.value) {
    validated.value = true
    return
  }
  validated.value = false
  submitting.value = true

  try {
    // targetType === 'project'일 때 extraData.project는 'bookmark'/'closed' 등의 필터 값이므로
    // CustomQuery.project FK가 아닌 filters.form 내부에 그대로 유지합니다.
    const extraProject = props.extraData?.project
    const resolvedProjectFk =
      props.projectId !== null
        ? props.projectId
        : props.targetType !== 'project' && typeof extraProject === 'number'
          ? extraProject
          : null

    const payload = {
      name: queryName.value,
      description: queryDescription.value.trim(),
      target_type: props.targetType,
      is_public: isPublic.value,
      project: resolvedProjectFk,
      filters: {
        ...props.extraFilters,
        searchCond: [...props.searchCond],
        cond: { ...props.cond },
        form: {
          ...props.form,
          ...(props.extraData || {}),
        },
      },
    }

    const created = await informStore.createQuery(payload)
    if (!created) return
    await informStore.fetchQueries({ targetType: props.targetType })
    closeModal()
    emit('saved')
  } finally {
    submitting.value = false
  }
}

defineExpose({ callModal, closeModal })
</script>

<template>
  <FormModal ref="refModal" size="lg">
    <template #header>검색양식 저장</template>
    <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="saveQuery">
      <CModalBody class="text-body">
        <CRow class="mb-3">
          <CFormLabel for="query-name" class="col-sm-3 col-form-label required text-end">
            양식 이름
          </CFormLabel>
          <CCol class="col-sm-9">
            <CFormInput
              id="query-name"
              v-model="queryName"
              placeholder="검색양식 이름을 입력하세요"
              required
            />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel for="query-desc" class="col-sm-3 col-form-label text-end"> 설명 </CFormLabel>
          <CCol class="col-sm-9">
            <CFormInput
              id="query-desc"
              v-model="queryDescription"
              placeholder="검색양식 설명을 입력하세요"
            />
          </CCol>
        </CRow>

        <CRow class="mb-3" v-if="can(PERM.PROJECT_PUB_QUERY)">
          <CCol class="offset-sm-3 col-sm-9">
            <CFormCheck id="query-is-public" v-model="isPublic" label="공용 (모든 사용자와 공유)" />
          </CCol>
        </CRow>
      </CModalBody>

      <CModalFooter>
        <v-btn
          type="submit"
          size="small"
          color="indigo"
          class="text-white"
          :loading="submitting"
          :disabled="submitting"
        >
          저장
        </v-btn>
        <v-btn color="grey" variant="tonal" size="small" @click="closeModal">취소</v-btn>
      </CModalFooter>
    </CForm>
  </FormModal>
</template>
