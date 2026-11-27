<script lang="ts" setup>
import { computed, ref } from 'vue'
import type { SiteContract } from '@/store/types/project'
import { usePerms } from '@/composables/usePerms'
import { AlertLight } from '@/utils/cssMixins'
import FormModal from '@/components/Modals/FormModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import SiteContractForm from './SiteContractForm.vue'

defineProps({ project: { type: Number, default: undefined } })
const emit = defineEmits(['multi-submit'])

const { can, PERM } = usePerms()
const canSiteCreate = computed(() => can(PERM.SITE_CREATE))

const refFormModal = ref()
const refAlertModal = ref()
const isFormVisible = ref(false)

const createConfirm = () => {
  if (canSiteCreate.value) {
    isFormVisible.value = true
    refFormModal.value.callModal()
  } else {
    refAlertModal.value.callModal()
  }
}

const handleClose = () => {
  refFormModal.value.close()
  isFormVisible.value = false
}

const multiSubmit = (payload: SiteContract) => {
  emit('multi-submit', payload, (ok: boolean) => {
    if (ok) handleClose()
  })
}
</script>

<template>
  <CAlert :color="AlertLight" variant="solid" class="text-end">
    <v-btn color="primary" :disabled="!project" @click="createConfirm">
      부지 매입계약 신규등록
    </v-btn>
  </CAlert>

  <FormModal ref="refFormModal" size="lg">
    <template #header>부지 매입 계약 등록</template>
    <template #default>
      <SiteContractForm
        v-if="isFormVisible"
        :project="project"
        @multi-submit="multiSubmit"
        @close="handleClose"
      />
    </template>
  </FormModal>

  <AlertModal ref="refAlertModal" />
</template>
