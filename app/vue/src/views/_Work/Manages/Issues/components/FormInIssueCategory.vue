<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { isValidate } from '@/utils/helper'
import { useAccount } from '@/store/pinia/account'

defineProps({
  memberList: { type: Array as PropType<{ pk: number; username: string }[]>, default: () => [] },
})
const emit = defineEmits(['create-category', 'close'])

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)

const validated = ref(false)

const nCategory = ref({
  name: '',
  assigned_to: null as number | null,
})

const resetForm = () => {
  nCategory.value = { name: '', assigned_to: null }
  validated.value = false
}

const createCategory = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    emit('create-category', { ...nCategory.value })
    resetForm()
    emit('close')
  }
}

const closeModal = () => {
  resetForm()
  emit('close')
}
</script>

<template>
  <CForm
    class="needs-validation"
    novalidate
    :validated="validated"
    @submit.prevent="createCategory"
  >
    <CModalBody class="text-body">
      <CRow class="mb-3">
        <CFormLabel for="category-name" class="col-3 col-form-label required text-end">
          이름
        </CFormLabel>
        <CCol class="col-7">
          <CFormInput id="category-name" v-model="nCategory.name" placeholder="새 업무 범주 이름" required />
        </CCol>
      </CRow>
      <CRow class="mb-3">
        <CFormLabel for="category-assigned-to" class="col-3 col-form-label text-end">
          담당자
        </CFormLabel>
        <CCol class="col-7">
          <CFormSelect id="category-assigned-to" v-model.number="nCategory.assigned_to">
            <option :value="null">---------</option>
            <option :value="userInfo?.pk">&lt;&lt; 나 &gt;&gt;</option>
            <option v-for="user in memberList" :value="user.pk" :key="user.pk">
              {{ user.username }}
            </option>
          </CFormSelect>
        </CCol>
      </CRow>
    </CModalBody>
    <CModalFooter>
      <v-btn type="submit" size="small" color="primary">저장</v-btn>
      <v-btn color="light" size="small" @click="closeModal" flat> 닫기</v-btn>
    </CModalFooter>
  </CForm>
</template>
