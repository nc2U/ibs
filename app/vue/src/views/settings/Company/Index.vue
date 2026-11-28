<script lang="ts" setup>
import { computed, ref } from 'vue'
import { navMenu, pageTitle } from '@/views/settings/_menu/headermixin'
import { useAccount } from '@/store/pinia/account'
import { useCompany } from '@/store/pinia/company'
import type { Company } from '@/store/types/settings'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import SettingsCompanyGuard from '@/components/AuthGuard/SettingsCompanyGuard.vue'
import CompanyForm from './components/CompanyForm.vue'
import CompanyDetail from './components/CompanyDetail.vue'

const compName = ref<'CompanyDetail' | 'CreateForm' | 'UpdateForm'>('CompanyDetail')
const isSubmitting = ref(false)

const account = useAccount()
const comStore = useCompany()
const company = computed(() => comStore.company)

const createForm = () => {
  if (!account.superAuth) return
  compName.value = 'CreateForm'
}
const updateForm = () => {
  if (!account.superAuth || !company.value?.pk) return
  compName.value = 'UpdateForm'
}
const resetForm = () => (compName.value = 'CompanyDetail')

const onSubmit = async (payload: Company) => {
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    const ok = payload.pk
      ? await comStore.updateCompany(payload)
      : await comStore.createCompany(payload)
    if (ok) resetForm()
  } finally {
    isSubmitting.value = false
  }
}

const onDelete = async (pk: number) => {
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    const ok = await comStore.deleteCompany(pk)
    if (ok) resetForm()
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <SettingsCompanyGuard>
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="CompanySelect"
      :selectable="compName === 'CompanyDetail'"
    />

    <ContentBody>
      <CompanyDetail
        v-if="compName === 'CompanyDetail'"
        :company="company as Company"
        @create-form="createForm"
        @update-form="updateForm"
      />

      <CompanyForm
        v-else-if="compName === 'CreateForm'"
        :company="null"
        :submitting="isSubmitting"
        @on-submit="onSubmit"
        @reset-form="resetForm"
      />

      <CompanyForm
        v-else-if="compName === 'UpdateForm'"
        :company="company as Company"
        :submitting="isSubmitting"
        @on-submit="onSubmit"
        @on-delete="onDelete"
        @reset-form="resetForm"
      />

      <template #footer>
        <div style="display: none"></div>
      </template>
    </ContentBody>
  </SettingsCompanyGuard>
</template>
