<script lang="ts" setup>
import { computed, ref } from 'vue'
import { type SiteContract } from '@/store/types/project'
import { usePerms } from '@/composables/usePerms.ts'
import { AlertLight } from '@/utils/cssMixins'
import FormModal from '@/components/Modals/FormModal.vue'
import SiteContractForm from './SiteContractForm.vue'

defineProps({ project: { type: Number, default: null } })
const emit = defineEmits(['multi-submit'])

const { can, PERM } = usePerms()
const canSiteCreate = computed(() => can(PERM.SITE_CREATE))

const refFormModal = ref()
const refAlertModal = ref()

const createConfirm = () => {
  if (canSiteCreate.value) refFormModal.value.callModal()
  else refAlertModal.value.callModal()
}
const multiSubmit = (payload: SiteContract) => emit('multi-submit', payload)
</script>

<template>
  <CAlert :color="AlertLight" variant="solid" class="text-right">
    <v-btn color="primary" :disabled="!project" @click="createConfirm">
      부지 매입계약 신규등록
    </v-btn>
  </CAlert>

  <FormModal ref="refFormModal" size="lg">
    <template #header>부지 매입 계약 등록</template>
    <template #default>
      <SiteContractForm
        :project="project"
        @multi-submit="multiSubmit"
        @close="refFormModal.close()"
      />
    </template>
  </FormModal>

  <AlertModal ref="refAlertModal" />
</template>
