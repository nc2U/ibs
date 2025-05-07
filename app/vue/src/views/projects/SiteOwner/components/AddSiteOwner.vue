<script lang="ts" setup>
import { ref } from 'vue'
import { type SiteOwner } from '@/store/types/project'
import { write_project } from '@/utils/pageAuth'
import { AlertLight } from '@/utils/cssMixins'
import FormModal from '@/components/Modals/FormModal.vue'
import SiteOwnerForm from '@/views/projects/SiteOwner/components/SiteOwnerForm.vue'

defineProps({ project: { type: Number, default: null } })
const emit = defineEmits(['multi-submit'])

const refFormModal = ref()
const refAlertModal = ref()

const createConfirm = () => {
  if (write_project.value) refFormModal.value.callModal()
  else refAlertModal.value.callModal()
}

const multiSubmit = (payload: SiteOwner) => emit('multi-submit', payload)
</script>

<template>
  <CAlert :color="AlertLight" variant="solid" class="text-right">
    <v-btn color="primary" :disabled="!project" @click="createConfirm">
      부지 소유자 신규등록
    </v-btn>
  </CAlert>

  <FormModal ref="refFormModal" size="lg">
    <template #header>부지 소유자 정보 등록</template>
    <template #default>
      <SiteOwnerForm @multi-submit="multiSubmit" @close="refFormModal.close()" />
    </template>
  </FormModal>

  <AlertModal ref="refAlertModal" />
</template>
