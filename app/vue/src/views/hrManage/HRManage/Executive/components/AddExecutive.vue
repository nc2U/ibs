<script lang="ts" setup>
import { computed, ref } from 'vue'
import { AlertSecondary } from '@/utils/cssMixins.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type Executive } from '@/store/types/company.ts'
import ExecutiveForm from './ExecutiveForm.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

defineProps<{ company?: string }>()
const emit = defineEmits<{
  (e: 'multi-submit', payload: Executive, done?: (ok: boolean) => void): void
}>()

const refFormModal = ref<InstanceType<typeof FormModal> | null>(null)
const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))

const createConfirm = () => {
  if (canHrWorkCreate.value) refFormModal.value?.callModal()
  else refAlertModal.value?.callModal()
}
const multiSubmit = (payload: Executive, done?: (ok: boolean) => void) =>
  emit('multi-submit', payload, done)
</script>

<template>
  <CAlert :color="AlertSecondary" class="text-end">
    <v-btn color="primary" :disabled="!company" @click="createConfirm">
      임원 재임 정보 신규등록
    </v-btn>
  </CAlert>

  <FormModal ref="refFormModal" size="lg">
    <template #header>임원 재임 정보 등록</template>
    <template #default>
      <ExecutiveForm :company="company" @multi-submit="multiSubmit" @close="refFormModal?.close()" />
    </template>
  </FormModal>

  <AlertModal ref="refAlertModal" />
</template>
