<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue'
import { pageTitle, navMenu1, navMenu2 } from '@/views/hrManage/_menu/headermixin2.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { useCompany } from '@/store/pinia/company.ts'
import type { Company } from '@/store/types/settings.ts'
import {
  type StaffCareer,
  type StaffCertificate,
  type StaffRewardPunishment,
  type StaffRecordFilter,
} from '@/store/types/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import ListController from './components/ListController.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import StaffCareerSection from './components/StaffCareerSection.vue'
import StaffCertificateSection from './components/StaffCertificateSection.vue'
import StaffRewardSection from './components/StaffRewardSection.vue'

const accStore = useAccount()
const { canGlobal, PERM } = usePerms()
const isHrManager = computed(
  () =>
    canGlobal(PERM.HQ_HR_WORK_READ) ||
    canGlobal(PERM.HQ_HR_WORK_CREATE) ||
    canGlobal(PERM.HQ_HR_WORK_UPDATE),
)
const navMenu = computed(() => (!isHrManager.value ? navMenu1 : navMenu2))

const currentTab = ref<'career' | 'certificate' | 'reward'>('career')

const dataFilter = ref<StaffRecordFilter>({
  page: 1,
  com: 1,
  staff: '',
  sort: '',
  q: '',
})

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)
const comName = computed(() => (comStore.company as Company)?.name || undefined)

const excelUrl = computed(() => {
  const filter = dataFilter.value
  let base = ''
  if (currentTab.value === 'career') base = '/excel/staff-careers/'
  else if (currentTab.value === 'certificate') base = '/excel/staff-certificates/'
  else base = '/excel/staff-rewards/'

  let query = `?company=${company.value}`
  if (filter.staff) query += `&staff=${filter.staff}`
  if (filter.sort && currentTab.value === 'reward') query += `&sort=${filter.sort}`
  if (filter.q) query += `&search=${filter.q}`
  return `${base}${query}`
})

const excelFilename = computed(() => {
  if (currentTab.value === 'career') return '직원_경력_이력.xlsx'
  if (currentTab.value === 'certificate') return '직원_자격_면허.xlsx'
  return '직원_상벌_이력.xlsx'
})

const listFiltering = (payload: StaffRecordFilter) => {
  dataFilter.value = payload
  if (company.value) {
    if (currentTab.value === 'career') fetchStaffCareerList(payload)
    else if (currentTab.value === 'certificate') fetchStaffCertificateList(payload)
    else fetchStaffRewardPunishmentList(payload)
  }
}

const fetchStaffCareerList = (payload: StaffRecordFilter) => comStore.fetchStaffCareerList(payload)
const fetchStaffCertificateList = (payload: StaffRecordFilter) =>
  comStore.fetchStaffCertificateList(payload)
const fetchStaffRewardPunishmentList = (payload: StaffRecordFilter) =>
  comStore.fetchStaffRewardPunishmentList(payload)
const fetchAllStaffList = (com?: number) => comStore.fetchAllStaffList(com)

// Career CRUD
const onCareerSubmit = (payload: StaffCareer) => {
  const { page } = dataFilter.value
  if (company.value) {
    if (payload.pk) comStore.updateStaffCareer(payload, page, company.value)
    else comStore.createStaffCareer(payload, page, company.value)
  }
}
const onCareerDelete = (pk: number) => {
  if (company.value) comStore.deleteStaffCareer(pk, company.value)
}

// Certificate CRUD
const onCertificateSubmit = (payload: StaffCertificate) => {
  const { page } = dataFilter.value
  if (company.value) {
    if (payload.pk) comStore.updateStaffCertificate(payload, page, company.value)
    else comStore.createStaffCertificate(payload, page, company.value)
  }
}
const onCertificateDelete = (pk: number) => {
  if (company.value) comStore.deleteStaffCertificate(pk, company.value)
}

// Reward CRUD
const onRewardSubmit = (payload: StaffRewardPunishment) => {
  const { page } = dataFilter.value
  if (company.value) {
    if (payload.pk) comStore.updateStaffRewardPunishment(payload, page, company.value)
    else comStore.createStaffRewardPunishment(payload, page, company.value)
  }
}
const onRewardDelete = (pk: number) => {
  if (company.value) comStore.deleteStaffRewardPunishment(pk, company.value)
}

const onPageSelect = (page: number) => {
  dataFilter.value.page = page
  listFiltering(dataFilter.value)
}

const onTabChange = (tab: 'career' | 'certificate' | 'reward') => {
  currentTab.value = tab
  dataFilter.value.page = 1
  if (company.value) {
    if (tab === 'career') fetchStaffCareerList(dataFilter.value)
    else if (tab === 'certificate') fetchStaffCertificateList(dataFilter.value)
    else fetchStaffRewardPunishmentList(dataFilter.value)
  }
}

const dataSetup = (pk: number) => {
  fetchStaffCareerList({ com: pk })
  fetchStaffCertificateList({ com: pk })
  fetchStaffRewardPunishmentList({ com: pk })
  fetchAllStaffList(pk)
}

const dataReset = () => {
  comStore.staffCareerList = []
  comStore.staffCertificateList = []
  comStore.staffRewardPunishmentList = []
  comStore.allStaffList = []
}

const comSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

const loading = ref(true)
onMounted(async () => {
  dataSetup(company.value || comStore.initComId)
  loading.value = false
})
</script>

<template>
  <ComHrAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="CompanySelect"
      @com-select="comSelect"
    />
    <ContentBody>
      <CCardBody>
        <ListController @list-filtering="listFiltering" />

        <!-- 탭 전환 네비게이션 -->
        <CNav variant="tabs" class="mb-3">
          <CNavItem>
            <CNavLink
              href="javascript:void(0);"
              :active="currentTab === 'career'"
              @click="onTabChange('career')"
            >
              <CIcon icon="cil-briefcase" class="me-1" />
              경력 사항
            </CNavLink>
          </CNavItem>
          <CNavItem>
            <CNavLink
              href="javascript:void(0);"
              :active="currentTab === 'certificate'"
              @click="onTabChange('certificate')"
            >
              <CIcon icon="cil-badge" class="me-1" />
              자격 및 면허
            </CNavLink>
          </CNavItem>
          <CNavItem>
            <CNavLink
              href="javascript:void(0);"
              :active="currentTab === 'reward'"
              @click="onTabChange('reward')"
            >
              <CIcon icon="cil-star" class="me-1" />
              상벌 이력
            </CNavLink>
          </CNavItem>
        </CNav>

        <!-- 탭 1: 경력 사항 -->
        <StaffCareerSection
          v-if="currentTab === 'career'"
          :company="comName"
          :excel-url="excelUrl"
          :excel-filename="excelFilename"
          :selected-staff="Number(dataFilter.staff) || undefined"
          @multi-submit="onCareerSubmit"
          @on-delete="onCareerDelete"
          @page-select="onPageSelect"
        />

        <!-- 탭 2: 자격 및 면허 -->
        <StaffCertificateSection
          v-if="currentTab === 'certificate'"
          :company="comName"
          :excel-url="excelUrl"
          :excel-filename="excelFilename"
          :selected-staff="Number(dataFilter.staff) || undefined"
          @multi-submit="onCertificateSubmit"
          @on-delete="onCertificateDelete"
          @page-select="onPageSelect"
        />

        <!-- 탭 3: 상벌 이력 -->
        <StaffRewardSection
          v-if="currentTab === 'reward'"
          :company="comName"
          :excel-url="excelUrl"
          :excel-filename="excelFilename"
          :selected-staff="Number(dataFilter.staff) || undefined"
          @multi-submit="onRewardSubmit"
          @on-delete="onRewardDelete"
          @page-select="onPageSelect"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
