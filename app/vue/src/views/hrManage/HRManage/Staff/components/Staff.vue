<script lang="ts" setup>
import { computed, ref } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { type Staff } from '@/store/types/company.ts'
import StaffForm from './StaffForm.vue'
import FormModal from '@/components/Modals/FormModal.vue'

defineProps<{ staff: Staff }>()
const emit = defineEmits<{
  (e: 'multi-submit', payload: Staff): void
  (e: 'on-delete', pk: number): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const updateFormModal = ref<InstanceType<typeof FormModal> | null>(null)

const badgeColor = ['', 'success', 'teal-darken-2', 'warning', 'error']

const showDetail = () => updateFormModal.value?.callModal()
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
      <a href="#" role="button" @click.prevent="showDetail">{{ staff.name }}</a>
    </CTableDataCell>
    <CTableDataCell class="text-start">{{ staff.email }}</CTableDataCell>
    <CTableDataCell>{{ staff.date_join }}</CTableDataCell>
    <CTableDataCell>
      <v-chip :color="badgeColor[staff.status]" variant="flat" size="x-small">
        {{ staff.status_desc }}
      </v-chip>
    </CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>직원 정보 상세 및 수정</template>
    <template #default>
      <StaffForm
        :staff="staff"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal?.close()"
      />
    </template>
  </FormModal>
</template>
