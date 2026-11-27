<script lang="ts" setup>
import { computed, ref } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { AlertSecondary } from '@/utils/cssMixins.ts'
import { type Position } from '@/store/types/company.ts'
import PositionForm from './PositionForm.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

defineProps<{
  company?: string | null
}>()

const emit = defineEmits<{
  (e: 'multi-submit', payload: Position, done?: (ok: boolean) => void): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))

const refFormModal = ref<InstanceType<typeof FormModal> | null>(null)
const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)

const createConfirm = () => {
  if (canHrWorkCreate.value) refFormModal.value?.callModal()
  else refAlertModal.value?.callModal()
}
const multiSubmit = (payload: Position, done?: (ok: boolean) => void) =>
  emit('multi-submit', payload, done)
</script>

<template>
  <CAlert :color="AlertSecondary" class="text-end">
    <v-btn color="primary" variant="flat" :disabled="!company" @click="createConfirm">
      직위 정보 신규등록
    </v-btn>
  </CAlert>

  <FormModal ref="refFormModal" size="lg">
    <template #header>직위 정보 등록</template>
    <template #default>
      <PositionForm
        :company="company"
        @multi-submit="multiSubmit"
        @close="refFormModal?.close()"
      />
    </template>
  </FormModal>

  <AlertModal ref="refAlertModal" />
</template>
