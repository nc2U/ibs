<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { navMenu1, navMenu2, pageTitle } from '@/views/hrManage/_menu/headermixin2.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import {
  type StaffCareer,
  type StaffCertificate,
  type StaffRecordFilter,
  type StaffRewardPunishment,
} from '@/store/types/company.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import ListController from './components/ListController.vue'
import StaffCareerSection from './components/StaffCareerSection.vue'
import StaffCertificateSection from './components/StaffCertificateSection.vue'
import StaffRewardSection from './components/StaffRewardSection.vue'

const { canGlobal, PERM } = usePerms()
const isHrManager = computed(
  () =>
    canGlobal(PERM.HQ_HR_WORK_READ) ||
    canGlobal(PERM.HQ_HR_WORK_CREATE) ||
    canGlobal(PERM.HQ_HR_WORK_UPDATE),
)
const navMenu = computed(() => (!isHrManager.value ? navMenu1 : navMenu2))

const currentTab = ref<'career' | 'certificate' | 'reward'>('career')
const refListControl = ref<InstanceType<typeof ListController> | null>(null)

const dataFilter = ref<StaffRecordFilter>({
  page: 1,
  com: undefined,
  staff: '',
  sort: '',
  q: '',
})

const comStore = useCompany()
const company = computed(() => comStore.company?.pk ?? undefined)
const comName = computed(() => comStore.company?.name || undefined)

const excelUrl = computed(() => {
  let base = '/excel/staff-rewards/'
  if (currentTab.value === 'career') base = '/excel/staff-careers/'
  else if (currentTab.value === 'certificate') base = '/excel/staff-certificates/'

  const sp = new URLSearchParams({ company: String(company.value ?? '') })
  const f = dataFilter.value
  if (f.staff) sp.set('staff', String(f.staff))
  if (f.sort && currentTab.value === 'reward') sp.set('sort', String(f.sort))
  if (f.q) sp.set('search', f.q)
  return `${base}?${sp.toString()}`
})

const excelFilename = computed(() => {
  if (currentTab.value === 'career') return '직원_경력_이력.xlsx'
  if (currentTab.value === 'certificate') return '직원_자격_면허.xlsx'
  return '직원_상벌_이력.xlsx'
})

const listFiltering = (payload: StaffRecordFilter) => {
  dataFilter.value = { ...payload, com: company.value }
  if (company.value) {
    if (currentTab.value === 'career') comStore.fetchStaffCareerList(dataFilter.value)
    else if (currentTab.value === 'certificate') comStore.fetchStaffCertificateList(dataFilter.value)
    else comStore.fetchStaffRewardPunishmentList(dataFilter.value)
  }
}

// Career CRUD
const onCareerSubmit = async (payload: StaffCareer, done?: (ok: boolean) => void) => {
  const { page } = dataFilter.value
  const ok = company.value
    ? payload.pk
      ? await comStore.updateStaffCareer(payload, page, company.value, dataFilter.value)
      : await comStore.createStaffCareer(payload, page, company.value, dataFilter.value)
    : false
  done?.(ok)
}
const onCareerDelete = async (pk: number, done?: (ok: boolean) => void) => {
  const ok = company.value
    ? await comStore.deleteStaffCareer(pk, company.value, dataFilter.value)
    : false
  if (ok) dataFilter.value.page = 1
  done?.(ok)
}

// Certificate CRUD
const onCertificateSubmit = async (payload: StaffCertificate, done?: (ok: boolean) => void) => {
  const { page } = dataFilter.value
  const ok = company.value
    ? payload.pk
      ? await comStore.updateStaffCertificate(payload, page, company.value, dataFilter.value)
      : await comStore.createStaffCertificate(payload, page, company.value, dataFilter.value)
    : false
  done?.(ok)
}
const onCertificateDelete = async (pk: number, done?: (ok: boolean) => void) => {
  const ok = company.value
    ? await comStore.deleteStaffCertificate(pk, company.value, dataFilter.value)
    : false
  if (ok) dataFilter.value.page = 1
  done?.(ok)
}

// Reward CRUD
const onRewardSubmit = async (payload: StaffRewardPunishment, done?: (ok: boolean) => void) => {
  const { page } = dataFilter.value
  const ok = company.value
    ? payload.pk
      ? await comStore.updateStaffRewardPunishment(payload, page, company.value, dataFilter.value)
      : await comStore.createStaffRewardPunishment(payload, page, company.value, dataFilter.value)
    : false
  done?.(ok)
}
const onRewardDelete = async (pk: number, done?: (ok: boolean) => void) => {
  const ok = company.value
    ? await comStore.deleteStaffRewardPunishment(pk, company.value, dataFilter.value)
    : false
  if (ok) dataFilter.value.page = 1
  done?.(ok)
}

const onPageSelect = (page: number) => {
  dataFilter.value.page = page
  listFiltering(dataFilter.value)
}

const onTabChange = (tab: 'career' | 'certificate' | 'reward') => {
  currentTab.value = tab
  dataFilter.value = { ...dataFilter.value, page: 1, com: company.value }
  if (company.value) {
    if (tab === 'career') comStore.fetchStaffCareerList(dataFilter.value)
    else if (tab === 'certificate') comStore.fetchStaffCertificateList(dataFilter.value)
    else comStore.fetchStaffRewardPunishmentList(dataFilter.value)
  }
}

const dataSetup = async (pk: number) => {
  await Promise.all([
    comStore.fetchStaffCareerList({ com: pk }),
    comStore.fetchStaffCertificateList({ com: pk }),
    comStore.fetchStaffRewardPunishmentList({ com: pk }),
    comStore.fetchAllStaffList(pk, ''),
  ])
}

const dataReset = () => {
  comStore.staffCareerList = []
  comStore.staffCareersCount = 0
  comStore.allStaffCareerList = []
  comStore.staffCareer = null
  comStore.staffCertificateList = []
  comStore.staffCertificatesCount = 0
  comStore.allStaffCertificateList = []
  comStore.staffCertificate = null
  comStore.staffRewardPunishmentList = []
  comStore.staffRewardPunishmentsCount = 0
  comStore.allStaffRewardPunishmentList = []
  comStore.staffRewardPunishment = null
  comStore.allStaffList = []
}

const loading = ref(true)
watch(
  company,
  async newVal => {
    dataReset()
    refListControl.value?.clearFilter()
    dataFilter.value = { page: 1, com: newVal, staff: '', sort: '', q: '' }
    if (newVal) {
      loading.value = true
      await dataSetup(newVal)
    }
    loading.value = false
  },
  { immediate: true },
)
</script>

<template>
  <ComHrAuthGuard require-hr-read>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="CompanySelect" />
    <ContentBody>
      <CCardBody>
        <ListController ref="refListControl" @list-filtering="listFiltering" />

        <!-- 탭 전환 네비게이션 -->
        <CNav variant="tabs" class="mb-3">
          <CNavItem>
            <CNavLink
              component="button"
              type="button"
              :active="currentTab === 'career'"
              @click="onTabChange('career')"
            >
              <CIcon icon="cil-briefcase" class="me-1" />
              경력 사항
            </CNavLink>
          </CNavItem>
          <CNavItem>
            <CNavLink
              component="button"
              type="button"
              :active="currentTab === 'certificate'"
              @click="onTabChange('certificate')"
            >
              <CIcon icon="cil-badge" class="me-1" />
              자격 및 면허
            </CNavLink>
          </CNavItem>
          <CNavItem>
            <CNavLink
              component="button"
              type="button"
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
          :active-page="dataFilter.page || 1"
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
          :active-page="dataFilter.page || 1"
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
          :active-page="dataFilter.page || 1"
          @multi-submit="onRewardSubmit"
          @on-delete="onRewardDelete"
          @page-select="onPageSelect"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
