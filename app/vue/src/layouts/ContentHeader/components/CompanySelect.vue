<script lang="ts" setup>
import { computed, onBeforeMount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import { useCompany } from '@/store/pinia/company'
import type { Company } from '@/store/types/settings.ts'
import Multiselect from '@vueform/multiselect'

defineProps({ selectable: { type: Boolean, default: true } })
const emit = defineEmits(['com-select'])

const { can, PERM } = usePerms()
const canProjectCreate = computed(() => can(PERM.PROJECT_CREATE))

const router = useRouter()
const route = useRoute()

const comStore = useCompany()
const company = computed(() => (comStore?.company as Company)?.pk)
const comSelectList = computed(() => comStore?.comSelect)

// URL에서 company 파라미터 읽기
const urlCompanyId = computed(() => {
  const id = route.query.company
  return id ? parseInt(id as string, 10) : null
})

const comSelect = (e: { originalEvent: Event; value: any; option: any }) => emit('com-select', e)
const comClear = () => emit('com-select', null)

onBeforeMount(async () => {
  await comStore?.fetchCompanyList()

  // URL에 company 파라미터가 있으면 해당 회사로, 없으면 기본 회사로
  const targetCompanyId = urlCompanyId.value || company.value || comStore.initComId
  if (targetCompanyId) await comStore.fetchCompany(targetCompanyId)
})
</script>

<template>
  <CRow class="m-0 align-items-center">
    <CFormLabel class="col-lg-1 col-form-label text-body">회사명</CFormLabel>
    <CCol md="6" lg="3">
      <Multiselect
        :value="company"
        :options="comSelectList as any[]"
        placeholder="회사선택"
        autocomplete="label"
        :classes="{ search: 'form-control multiselect-search' }"
        :add-option-on="['enter', 'tab']"
        searchable
        :disabled="!selectable"
        @select="comSelect"
        @clear="comClear"
      />
    </CCol>
    <CCol v-if="!comSelectList?.length" class="pl-0 align-middle">
      <v-icon
        icon="mdi mdi-plus-thick"
        color="primary"
        :disabled="!canProjectCreate"
        @click="router.push({ name: '회사 정보 관리' })"
      />
      <v-tooltip v-if="!canProjectCreate" activator="parent" location="end">
        회사 및 프로젝트 생성 권한이 필요합니다.
      </v-tooltip>
    </CCol>
  </CRow>
</template>
