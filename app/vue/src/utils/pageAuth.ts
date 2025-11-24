import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'

export const isSuperUser = computed(() => useAccount().superAuth)

export const read_contract = computed(
  () => isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.contract !== '0'),
)

export const write_contract = computed(
  () => isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.contract === '2'),
)

export const read_payment = computed(
  () => isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.payment !== '0'),
)

export const write_payment = computed(
  () => isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.payment === '2'),
)

export const read_notice = computed(
  () => isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.notice !== '0'),
)

export const write_notice = computed(
  () => isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.notice === '2'),
)

export const read_project_cash = computed(
  () =>
    isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.project_ledger !== '0'),
)

export const write_project_cash = computed(
  () =>
    isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.project_ledger === '2'),
)

export const read_project_docs = computed(
  () =>
    isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.project_docs !== '0'),
)

export const write_project_docs = computed(
  () =>
    isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.project_docs === '2'),
)

export const read_project = computed(
  () => isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.project !== '0'),
)

export const write_project = computed(
  () => isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.project === '2'),
)

export const read_project_site = computed(
  () =>
    isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.project_site !== '0'),
)

export const write_project_site = computed(
  () =>
    isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.project_site === '2'),
)

export const read_company_cash = computed(
  () =>
    isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.company_ledger !== '0'),
)

export const write_company_cash = computed(
  () =>
    isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.company_ledger === '2'),
)

export const read_company_docs = computed(
  () =>
    isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.company_docs !== '0'),
)

export const write_company_docs = computed(
  () =>
    isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.company_docs === '2'),
)

export const read_human_resource = computed(
  () =>
    isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.human_resource !== '0'),
)

export const write_human_resource = computed(
  () =>
    isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.human_resource === '2'),
)

export const read_company_settings = computed(
  () =>
    isSuperUser.value ||
    (useAccount().staffAuth && useAccount().staffAuth?.company_settings !== '0'),
)

export const write_company_settings = computed(
  () =>
    isSuperUser.value ||
    (useAccount().staffAuth && useAccount().staffAuth?.company_settings === '2'),
)

export const read_auth_manage = computed(
  () =>
    isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.auth_manage !== '0'),
)

export const write_auth_manage = computed(
  () =>
    isSuperUser.value || (useAccount().staffAuth && useAccount().staffAuth?.auth_manage === '2'),
)
