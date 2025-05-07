<script lang="ts" setup>
import { ref, computed, onBeforeMount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import ResetForm from '@/views/_Accounts/components/ResetForm.vue'
import SocialLogin from '@/views/_Accounts/components/SocialLogin.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const refAlertModal = ref()

const accStore = useAccount()
const [route, router] = [useRoute(), useRouter()]

const uid = computed(() => Number(atob(route.query.uidb64 as string)))
const token = computed(() => route.query.token)
const isExpired = computed(() => {
  const resetToken = accStore.resetTokenList.length ? accStore.resetTokenList[0] : null
  if (!!resetToken) {
    if (resetToken.is_expired)
      return true // expired!
    else return token.value !== resetToken.token // if tokenCheck true -> not expired!, false -> expired!
  } else return true
})

const fetchResetTokenList = (user: number) => accStore.fetchResetTokenList(user)

const onSubmit = async (new_password: string) => {
  const payload = {
    user_id: route.query.uidb64,
    token: route.query.token,
    new_password,
  }
  accStore.passResetConfirm(payload)
  await refAlertModal.value.callModal()
}

onBeforeMount(() => fetchResetTokenList(uid.value))
</script>

<template>
  <div class="bg-light min-vh-100 d-flex flex-row align-items-center">
    <CContainer>
      <CRow class="justify-content-center">
        <CCol md="8" lg="6" xl="4">
          <CCard class="p-4">
            <CCardBody v-if="isExpired" class="text-center text-danger">
              <h2>This Token was Expired!</h2>
              <div class="text-left pt-3">
                <p class="text-muted">
                  이 토큰의 비밀번호 재설정 가능시간이 만료되었습니다. 비밀번호를 재설정 하려면 다시
                  요청해 주십시요.
                </p>
              </div>
              <div class="text-right pt-2">
                <router-link :to="{ name: 'Login' }">To Login</router-link>
              </div>
            </CCardBody>
            <CCardBody v-else class="text-body">
              <ResetForm @on-submit="onSubmit" />

              <SocialLogin />
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>
    </CContainer>
  </div>

  <AlertModal ref="refAlertModal">
    <template #header>성공!</template>
    <template #default>비밀번호가 변경되었습니다. 새 비밀번호로 다시 로그인하십시오.</template>
    <template #footer>
      <v-btn color="primary" @click="router.push({ name: 'Home' })">지금 로그인</v-btn>
    </template>
  </AlertModal>
</template>
