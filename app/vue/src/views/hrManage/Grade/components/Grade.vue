<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useCompany } from '@/store/pinia/company'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type Grade } from '@/store/types/company'
import FormModal from '@/components/Modals/FormModal.vue'
import StaffForm from './GradeForm.vue'

const props = defineProps({
  grade: { type: Object as PropType<Grade>, required: true },
})

const emit = defineEmits(['multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkManage = computed(
  () => accStore.isStaff && (can(PERM.HR_WORK_CREATE) || can(PERM.HR_WORK_UPDATE)),
)

const updateFormModal = ref()

const comStore = useCompany()
const pkPositions = computed(() => comStore.getPkPositions)

const positions = computed(() => {
  const ids = props.grade.positions || []
  return pkPositions.value
    .filter(p => ids.includes(p.value as number))
    .map(p => p.label)
    .join(', ')
})

const showDetail = () => updateFormModal.value.callModal()
const multiSubmit = (payload: Grade) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTableRow v-if="grade" class="text-center">
    <CTableDataCell>{{ grade.pk }}</CTableDataCell>
    <CTableDataCell>{{ grade.code }}</CTableDataCell>
    <CTableDataCell class="text-left">{{ grade.role }}</CTableDataCell>
    <CTableDataCell>{{ grade.min_promotion_years ?? '-' }}</CTableDataCell>
    <CTableDataCell class="text-left">{{ positions }}</CTableDataCell>
    <CTableDataCell class="text-left">{{ grade.promotion_criteria }}</CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>직급 정보 등록</template>
    <template #default>
      <StaffForm
        :grade="grade"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
