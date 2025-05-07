<script lang="ts" setup>
import { type ComputedRef, inject, type PropType, ref } from 'vue'
import { isValidate } from '@/utils/helper'
import type { User } from '@/store/types/accounts'

defineProps({
  memberList: { type: Array as PropType<{ pk: number; username: string }[]>, default: () => [] },
})
const emit = defineEmits(['create-category', 'close'])
const userInfo = inject<ComputedRef<User>>('userInfo')

const validated = ref(false)

const nCategory = ref({
  name: '',
  assigned_to: null,
})

const createCategory = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    emit('create-category', { ...nCategory.value })
    validated.value = false
    emit('close')
  }
}

const closeModal = () => emit('close')
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
        <CFormLabel for="category-name" class="col-3 col-form-label required text-right">
          이름
        </CFormLabel>
        <CCol class="col-7">
          <CFormInput v-model="nCategory.name" placeholder="새 업무 범주 이름" required />
        </CCol>
      </CRow>
      <CRow class="mb-3">
        <CFormLabel for="category-name" class="col-3 col-form-label text-right">
          담당자
        </CFormLabel>
        <CCol class="col-7">
          <CFormSelect v-model.number="nCategory.assigned_to">
            <option value="">---------</option>
            <option :value="userInfo?.pk">&lt;&lt; 나 &gt;&gt;</option>
            <option v-for="user in memberList" :value="user.pk" :key="user.pk">
              {{ user.username }}
            </option>
          </CFormSelect>
        </CCol>
      </CRow>
    </CModalBody>
    <CModalFooter>
      <v-btn color="light" @click="closeModal"> 닫기</v-btn>
      <v-btn type="submit" color="primary">저장</v-btn>
    </CModalFooter>
  </CForm>
</template>
