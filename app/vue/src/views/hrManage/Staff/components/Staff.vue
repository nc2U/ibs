<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import { type Staff } from '@/store/types/company'
import FormModal from '@/components/Modals/FormModal.vue'
import StaffForm from './StaffForm.vue'
import { write_human_resource } from '@/utils/pageAuth'

defineProps({
  staff: { type: Object as PropType<Staff>, required: true },
})

const emit = defineEmits(['multi-submit', 'on-delete'])

const updateFormModal = ref()

const badgeColor = ['', 'success', 'teal-darken-2', 'warning', 'danger']

const showDetail = () => updateFormModal.value.callModal()
const multiSubmit = (payload: Staff) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTableRow v-if="staff" class="text-center">
    <CTableDataCell>{{ staff.sort_desc }}</CTableDataCell>
    <CTableDataCell>{{ staff.department }}</CTableDataCell>
    <CTableDataCell>{{ staff.position }}</CTableDataCell>
    <CTableDataCell>{{ staff.duty }}</CTableDataCell>
    <CTableDataCell>
      <a href="javascript:void(0);" @click="showDetail">{{ staff.name }}</a>
    </CTableDataCell>
    <CTableDataCell class="text-left">{{ staff.email }}</CTableDataCell>
    <CTableDataCell>{{ staff.date_join }}</CTableDataCell>
    <CTableDataCell>
      <CBadge :color="badgeColor[staff.status]">
        {{ staff.status_desc }}
      </CBadge>
    </CTableDataCell>
    <CTableDataCell v-if="write_human_resource">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>직원 정보 등록</template>
    <template #default>
      <StaffForm
        :staff="staff"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
