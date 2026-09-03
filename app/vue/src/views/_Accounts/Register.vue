<script setup lang="ts">
import router from '@/router'
import { useAccount } from '@/store/pinia/account'
import RegisterForm from './components/RegisterForm.vue'
import SocialLogin from '@/views/_Accounts/components/SocialLogin.vue'
import ThemeSwitcher from '@/components/ThemeSwitcher/Index.vue'

interface SignUser {
  email: string
  username: string
  password: string
}

const accountStore = useAccount()

const onSubmit = (payload: SignUser) => {
  accountStore.signup(payload)
  router.replace({ name: 'Login' })
}
</script>

<template>
  <div class="bg-light min-vh-100 d-flex flex-row align-items-center">
    <div class="position-fixed top-0 end-0 p-3" style="z-index: 1050">
      <ThemeSwitcher size="lg" tooltip-location="bottom" />
    </div>
    <CContainer>
      <CRow class="justify-content-center">
        <CCol md="9" lg="7" xl="5">
          <CCard class="mx-4 p-4">
            <CCardBody class="text-body">
              <RegisterForm @on-submit="onSubmit" />

              <SocialLogin />
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>
    </CContainer>
  </div>
</template>
