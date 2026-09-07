<script lang="ts" setup>
import { ref, reactive } from 'vue'
import { useSales } from '@/store/pinia/sales'
import type { SalesAgency } from '@/store/types/sales'
import FormModal from '@/components/Modals/FormModal.vue'
import { CModalBody, CRow } from '@coreui/vue'

const props = defineProps({
  project: { type: Number, required: true },
})

const emit = defineEmits(['saved'])

const salesStore = useSales()
const modalRef = ref()
const isEdit = ref(false)
const targetId = ref<number | null>(null)

const form = reactive({
  name: '',
  is_direct_managed: true,
  business_number: '',
  ceo_name: '',
  phone: '',
  order: 1,
  is_active: true,
})

const resetForm = () => {
  form.name = ''
  form.is_direct_managed = true
  form.business_number = ''
  form.ceo_name = ''
  form.phone = ''
  form.order = 1
  form.is_active = true
  targetId.value = null
  isEdit.value = false
}

const open = (agency?: SalesAgency) => {
  resetForm()
  if (agency) {
    isEdit.value = true
    targetId.value = agency.id
    form.name = agency.name
    form.is_direct_managed = agency.is_direct_managed
    form.business_number = agency.business_number
    form.ceo_name = agency.ceo_name
    form.phone = agency.phone
    form.order = agency.order
    form.is_active = agency.is_active
  }
  modalRef.value.callModal()
}

const submit = async () => {
  if (!form.name.trim()) {
    alert('대행사명을 입력해주세요.')
    return
  }
  const payload = {
    ...form,
    project: props.project,
  }

  if (isEdit.value && targetId.value) {
    await salesStore.updateAgency(targetId.value, payload)
  } else {
    await salesStore.createAgency(payload)
  }
  modalRef.value.close()
  emit('saved')
}

defineExpose({ open })
</script>

<template>
  <FormModal ref="modalRef" size="lg">
    <template #header>{{ isEdit ? '분양 대행사 수정' : '신규 분양 대행사 등록' }}</template>
    <template #default>
      <CModalBody>
        <CRow class="g-3">
          <CCol md="8">
            <CFormLabel>대행사명 <span class="text-danger">*</span></CFormLabel>
            <CFormInput
              v-model="form.name"
              placeholder="예: [직영] 자체 분양팀 또는 (주)미래분양대행"
              required
              @keydown.enter="submit"
            />
          </CCol>
          <CCol md="4" class="d-flex align-items-center pt-4">
            <CFormCheck
              id="is_direct_managed"
              v-model="form.is_direct_managed"
              label="자체 직영 대행 여부"
            />
          </CCol>
          <CCol md="4">
            <CFormLabel>대표자명</CFormLabel>
            <CFormInput v-model="form.ceo_name" placeholder="대표자 성명" @keydown.enter="submit" />
          </CCol>
          <CCol md="4">
            <CFormLabel>사업자등록번호</CFormLabel>
            <input
              v-model="form.business_number"
              v-maska
              data-maska="###-##-#####"
              class="form-control"
              placeholder="000-00-00000"
              @keydown.enter="submit"
            />
          </CCol>
          <CCol md="4">
            <CFormLabel>대표 전화번호</CFormLabel>
            <input
              v-model="form.phone"
              v-maska
              data-maska="['###-###-####', '###-####-####']"
              class="form-control"
              placeholder="02-000-0000"
              @keydown.enter="submit"
            />
          </CCol>
          <CCol md="4">
            <CFormLabel>정렬 순서</CFormLabel>
            <CFormInput v-model.number="form.order" type="number" min="1" @keydown.enter="submit" />
          </CCol>
          <CCol md="4" class="d-flex align-items-center pt-4">
            <CFormCheck id="is_active" v-model="form.is_active" label="사용 여부 (활성화)" />
          </CCol>
        </CRow>
      </CModalBody>
      <CModalFooter>
        <v-btn color="primary" size="small" @click="submit">
          {{ isEdit ? '수정 저장' : '등록하기' }}
        </v-btn>
        <v-btn color="light" size="small" flat @click="modalRef.close()">취소</v-btn>
      </CModalFooter>
    </template>
  </FormModal>
</template>
