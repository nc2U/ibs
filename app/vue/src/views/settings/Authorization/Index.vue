<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/settings/_menu/headermixin'
import { type User } from '@/store/types/accounts'
import { useCompany } from '@/store/pinia/company'
import { useAccount, type UserByAdmin } from '@/store/pinia/account'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import AuthManageAuthGuard from '@/components/AuthGuard/AuthManageAuthGuard.vue'
import UserSelect from './components/UserSelect.vue'
import SideBarManageAuth from './components/SideBarManageAuth.vue'
import AddUserFormModal from './components/AddUserFormModal.vue'

const refFormModal = ref()

const comInfo = ref<{ company: number | null; is_hq_staff: boolean }>({
  company: null,
  is_hq_staff: false,
})

const changeStaff = (val: boolean) => {
  comInfo.value.is_hq_staff = val
  projectAuth.value.is_pjt_staff = !val
}

const projectAuth = ref({
  is_pjt_staff: false,
  allowed_projects: [] as number[],
  default_project: null as number | null,
})

const changeProStaff = (val: boolean) => {
  projectAuth.value.is_pjt_staff = val
  comInfo.value.is_hq_staff = !val
}

const comStore = useCompany()
const comId = computed(() => comStore.company?.pk)
const fetchCompany = async (pk: number) => await comStore.fetchCompany(pk)

const accStore = useAccount()
const user = computed<User | null>(() => accStore.user)

const adminCreateUser = (payload: UserByAdmin) => accStore.adminCreateUser(payload)

const selectUser = (pk: number | null) => {
  if (!!pk) {
    accStore.fetchUser(pk).then(() => {
      if (user.value && !user.value.staff_auth) authReset()
    })
  } else {
    accStore.removeUser()
    authReset()
  }
}

const getAllowed = (payload: number[]) => (projectAuth.value.allowed_projects = payload)
const getAssigned = (payload: number | null) => (projectAuth.value.default_project = payload)

const authReset = () => {
  comInfo.value.is_hq_staff = false
  projectAuth.value.is_pjt_staff = false
  projectAuth.value.default_project = null
  projectAuth.value.allowed_projects = []
}

const onSubmit = (payload: any) => {
  console.log(payload)
  adminCreateUser(payload)
}

watch(
  () => user.value?.staff_auth,
  nVal => {
    if (nVal) {
      comInfo.value.is_hq_staff = nVal.is_hq_staff
      projectAuth.value.is_pjt_staff = nVal.is_pjt_staff
      projectAuth.value.default_project = nVal.default_project
      projectAuth.value.allowed_projects = nVal.allowed_projects
    }
  },
)

watch(comId, async val => (!!val ? await dataSetup(val) : dataReset()))

const dataSetup = async (pk: number) => {
  await fetchCompany(pk)
  comInfo.value.company = pk
}

const dataReset = () => (comInfo.value.company = null)

const loading = ref(true)
onBeforeMount(async () => {
  await accStore.fetchUsersList()
  comInfo.value.company = comId.value || comStore.initComId
  if (accStore?.userInfo) selectUser((accStore.userInfo as User).pk as number)
  loading.value = false
})
</script>

<template>
  <AuthManageAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="CompanySelect" />
    <ContentBody>
      <CCardBody>
        <UserSelect
          :sel-user="user?.pk"
          :is-staff="comInfo.is_hq_staff"
          :is-project-staff="projectAuth.is_pjt_staff"
          @change-staff="changeStaff"
          @change-pro-staff="changeProStaff"
          @select-user="selectUser"
          @add-user-modal="refFormModal.callModal()"
        />

        <SideBarManageAuth
          :user="user as User"
          :allowed="projectAuth.allowed_projects"
          @get-allowed="getAllowed"
          @get-assigned="getAssigned"
        />
      </CCardBody>

      <AddUserFormModal ref="refFormModal" @on-submit="onSubmit" />
    </ContentBody>
  </AuthManageAuthGuard>
</template>
