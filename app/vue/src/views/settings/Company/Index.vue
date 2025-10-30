<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { navMenu, pageTitle } from '@/views/settings/_menu/headermixin'
import { useCompany } from '@/store/pinia/company'
import { type Company } from '@/store/types/settings'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import CompanySettingsAuthGuard from '@/components/AuthGuard/CompanySettingsAuthGuard.vue'
import CompanyForm from './components/CompanyForm.vue'
import CompanyDetail from './components/CompanyDetail.vue'

const compName = ref('CompanyDetail')

const comStore = useCompany()
const company = computed(() => comStore.company)

const createCompany = (payload: Company) => comStore.createCompany(payload)
const updateCompany = (payload: Company) => comStore.updateCompany(payload)

const createForm = () => (compName.value = 'CreateForm')
const updateForm = () => (compName.value = 'UpdateForm')
const resetForm = () => (compName.value = 'CompanyDetail')

const onCreate = (payload: Company) => createCompany(payload)
const onUpdate = (payload: Company) => updateCompany(payload)

const onSubmit = (payload: Company) => {
  if (payload.pk) onUpdate(payload)
  else onCreate(payload)
}

const RefCompanyForm = ref()
const dataSet = () => RefCompanyForm.value.formDataSetup()

const loading = ref(true)
onBeforeMount(() => {
  loading.value = false
})
</script>

<template>
  <CompanySettingsAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="CompanySelect"
      @com-select="dataSet"
    />

    <ContentBody>
      <CompanyDetail
        v-if="compName === 'CompanyDetail'"
        :company="company as Company"
        @create-form="createForm"
        @update-form="updateForm"
      />

      <CompanyForm v-if="compName === 'CreateForm'" @on-submit="onSubmit" @reset-form="resetForm" />

      <CompanyForm
        ref="RefCompanyForm"
        v-if="compName === 'UpdateForm'"
        :company="company as Company"
        @on-submit="onSubmit"
        @reset-form="resetForm"
      />

      <template #footer>
        <div style="display: none"></div>
      </template>
    </ContentBody>
  </CompanySettingsAuthGuard>
</template>
