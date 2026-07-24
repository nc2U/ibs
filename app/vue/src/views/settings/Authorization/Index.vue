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

const comInfo = ref<{ company: number | null }>({
  company: null,
})

const comStore = useCompany()
const comId = computed(() => comStore.company?.pk)
const fetchCompany = async (pk: number) => await comStore.fetchCompany(pk)

const accStore = useAccount()
const user = computed<User | null>(() => accStore.user)

const adminCreateUser = (payload: UserByAdmin) => accStore.adminCreateUser(payload)

const selectUser = (pk: number | null) => {
  if (!!pk) {
    accStore.fetchUser(pk)
  } else {
    accStore.removeUser()
  }
}

const onSubmit = (payload: any) => {
  console.log(payload)
  adminCreateUser(payload)
}

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
          @select-user="selectUser"
          @add-user-modal="refFormModal.callModal()"
        />

        <SideBarManageAuth
          :user="user as User"
        />
      </CCardBody>

      <AddUserFormModal ref="refFormModal" @on-submit="onSubmit" />
    </ContentBody>
  </AuthManageAuthGuard>
</template>
