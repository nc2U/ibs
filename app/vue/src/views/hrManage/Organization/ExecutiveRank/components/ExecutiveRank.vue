<script lang="ts" setup>
import { computed, ref } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { type ExecutiveRank } from '@/store/types/company.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import ExecutiveRankForm from './ExecutiveRankForm.vue'

defineProps<{
  executiveRank: ExecutiveRank
}>()

const emit = defineEmits<{
  (e: 'multi-submit', payload: ExecutiveRank, done?: (ok: boolean) => void): void
  (e: 'on-delete', pk: number, done?: (ok: boolean) => void): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const updateFormModal = ref<InstanceType<typeof FormModal> | null>(null)

const showDetail = () => updateFormModal.value?.callModal()
const multiSubmit = (payload: ExecutiveRank, done?: (ok: boolean) => void) =>
  emit('multi-submit', payload, done)
const onDelete = (pk: number, done?: (ok: boolean) => void) => emit('on-delete', pk, done)
</script>

<template>
  <CTableRow v-if="executiveRank" class="text-center">
    <CTableDataCell>{{ executiveRank.sort_order }}</CTableDataCell>
    <CTableDataCell>{{ executiveRank.code }}</CTableDataCell>
    <CTableDataCell>{{ executiveRank.name }}</CTableDataCell>
    <CTableDataCell class="text-start">{{ executiveRank.role_desc }}</CTableDataCell>
    <CTableDataCell v-if="canHrWorkManage">
      <v-btn color="info" variant="flat" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>임원 직위 정보 수정</template>
    <template #default>
      <ExecutiveRankForm
        :executive-rank="executiveRank"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal?.close()"
      />
    </template>
  </FormModal>
</template>
