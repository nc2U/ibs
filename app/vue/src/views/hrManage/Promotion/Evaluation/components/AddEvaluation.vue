<script lang="ts" setup>
import { computed, ref } from 'vue'
import { AlertSecondary } from '@/utils/cssMixins.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type StaffEvaluation } from '@/store/types/company.ts'
import EvaluationForm from './EvaluationForm.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

defineProps<{ company?: string | null }>()
const emit = defineEmits<{
  (e: 'multi-submit', payload: StaffEvaluation, done?: (ok: boolean) => void): void
}>()

const refFormModal = ref<InstanceType<typeof FormModal> | null>(null)
const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))

const createConfirm = () => {
  if (canHrWorkCreate.value) refFormModal.value?.callModal()
  else refAlertModal.value?.callModal()
}
const multiSubmit = (payload: StaffEvaluation, done?: (ok: boolean) => void) =>
  emit('multi-submit', payload, done)
</script>

<template>
  <CAlert :color="AlertSecondary" class="text-end">
    <v-btn color="primary" variant="flat" :disabled="!company" @click="createConfirm">
      인사 평가 기록 등록
    </v-btn>
  </CAlert>

  <FormModal ref="refFormModal" size="lg">
    <template #header>인사 평가 기록 등록</template>
    <template #default>
      <EvaluationForm
        :company="company"
        @multi-submit="multiSubmit"
        @close="refFormModal?.close()"
      />
    </template>
  </FormModal>

  <AlertModal ref="refAlertModal" />
</template>
