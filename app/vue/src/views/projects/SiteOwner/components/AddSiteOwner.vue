<script lang="ts" setup>
import { computed, ref } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { AlertLight } from '@/utils/cssMixins'
import { type SiteOwner } from '@/store/types/project'
import FormModal from '@/components/Modals/FormModal.vue'
import SiteOwnerForm from '@/views/projects/SiteOwner/components/SiteOwnerForm.vue'

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
