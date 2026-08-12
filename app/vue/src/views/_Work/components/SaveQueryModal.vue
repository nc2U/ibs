<script lang="ts" setup>
import { ref, type PropType } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms'
import { useInform } from '@/store/pinia/work_inform.ts'
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
    type: Object as PropType<Record<string, any>>,
    required: true,
  },
  form: {
    type: Object as PropType<Record<string, any>>,
    required: true,
  },
  extraData: {
    type: Object as PropType<Record<string, any>>,
    default: () => ({}),
  },
})

const emit = defineEmits<{
  (e: 'saved'): void
}>()

const refModal = ref()
const { can, PERM } = usePerms()
const informStore = useInform()

const queryName = ref('')
const queryDescription = ref('')
const isPublic = ref(false)
const validated = ref(false)

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

  const { project: extraProject, ...otherExtraData } = props.extraData || {}

  const payload = {
    name: queryName.value,
    description: queryDescription.value,
    target_type: props.targetType,
    is_public: isPublic.value,
    project: extraProject || null,
    filters: {
      searchCond: props.searchCond,
      cond: props.cond,
      form: {
        ...props.form,
        ...otherExtraData,
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
          <CFormLabel for="query-name" class="col-sm-3 col-form-label required text-right">
            양식 이름
          </CFormLabel>
          <CCol class="col-sm-9">
            <CFormInput id="query-name" v-model="queryName" placeholder="검색양식 이름을 입력하세요" required />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel for="query-desc" class="col-sm-3 col-form-label text-right"> 설명 </CFormLabel>
          <CCol class="col-sm-9">
            <CFormInput id="query-desc" v-model="queryDescription" placeholder="검색양식 설명을 입력하세요" />
          </CCol>
        </CRow>

        <CRow class="mb-3" v-if="can(PERM.PROJECT_PUB_QUERY)">
          <CCol class="offset-sm-3 col-sm-9">
            <CFormCheck id="query-is-public" v-model="isPublic" label="공용 (모든 사용자와 공유)" />
          </CCol>
        </CRow>
      </CModalBody>

      <CModalFooter>
        <v-btn type="submit" size="small" color="indigo" class="text-white">저장</v-btn>
        <v-btn color="light" size="small" @click="closeModal" flat>취소</v-btn>
      </CModalFooter>
    </CForm>
  </FormModal>
</template>
