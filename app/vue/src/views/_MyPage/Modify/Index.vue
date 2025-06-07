<script lang="ts" setup>
import { ref, computed, onBeforeMount } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { useRouter } from 'vue-router'
import { pageTitle, navMenu } from '@/views/_MyPage/_menu/headermixin'
import type { Profile, User } from '@/store/types/accounts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import PasswordCheck from '@/views/_MyPage/Modify/components/PasswordCheck.vue'
import ProfileForm from '@/views/_MyPage/Modify/components/ProfileForm.vue'
import PasswordChange from '@/views/_MyPage/Modify/components/PasswordChange.vue'

const passChangeVue = ref(false)

const accStore = useAccount()
const userInfo = computed<User | null>(() => accStore.userInfo)
const profile = computed(() => accStore.profile)
const passChecked = computed(() => accStore.passChecked)

const checkPassword = (payload: { email: string; password: string }) =>
  accStore.checkPassword(payload)
const changePassword = (payload: { old_password: string; new_password: string }) =>
  accStore.changePassword(payload)
const createProfile = (payload: FormData) => accStore.createProfile(payload)
const patchProfile = (payload: { pk: number; form: FormData }) => accStore.patchProfile(payload)

const checkPass = (password: string) => {
  const email = userInfo.value?.email ?? ''
  checkPassword({ email, password })
}

const router = useRouter()

const changePass = async (payload: { old_password: string; new_password: string }) => {
  if (await changePassword(payload))
    setTimeout(() => {
      router.push({ name: 'Login' })
    }, 1000)
}

const callPassVue = () => (passChangeVue.value = true)

const onSubmit = (payload: Profile) => {
  if (!payload.image) delete payload.image

  const { pk, ...formData } = payload
  if (!formData.user && userInfo.value) formData.user = userInfo.value?.pk
  if (!formData.birth_date) formData.birth_date = ''

  const form = new FormData()

  for (const key in formData) form.append(key, formData[key] as string | Blob)

  if (pk) patchProfile({ ...{ pk }, ...{ form } })
  else createProfile(form)
}

const loading = ref(true)
onBeforeMount(() => {
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" />

  <ContentBody>
    <PasswordChange
      v-if="passChangeVue"
      :username="userInfo?.username"
      @change-password="changePass"
    />
    <PasswordCheck
      v-else-if="!passChecked"
      :username="userInfo?.username"
      @check-password="checkPass"
    />
    <ProfileForm
      v-else
      ref="profile"
      :user-info="userInfo"
      :profile="profile as Profile"
      @pass-change="callPassVue"
      @on-submit="onSubmit"
    />

    <template #footer>
      <small v-if="passChecked" />
    </template>
  </ContentBody>
</template>
