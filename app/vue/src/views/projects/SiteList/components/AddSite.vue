<script lang="ts" setup>
import { computed, ref } from 'vue'
import { AlertLight } from '@/utils/cssMixins'
import { usePerms } from '@/composables/usePerms.ts'
import { type Site } from '@/store/types/project'
import FormModal from '@/components/Modals/FormModal.vue'
import SiteForm from './SiteForm.vue'

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
const multiSubmit = (payload: Site) => emit('multi-submit', payload)
</script>

<template>
  <CAlert :color="AlertLight" variant="solid" class="text-right">
    <v-btn color="primary" :disabled="!project" @click="createConfirm"> 사업 부지 신규등록 </v-btn>
  </CAlert>

  <FormModal ref="refFormModal" size="lg">
    <template #header>사업 부지 등록</template>
    <template #default>
      <SiteForm @multi-submit="multiSubmit" @close="refFormModal.close()" />
    </template>
  </FormModal>

  <AlertModal ref="refAlertModal" />
</template>
