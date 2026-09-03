<script lang="ts" setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import LoginForm from './components/LoginForm.vue'
import FindPassword from '@/views/_Accounts/components/FindPassword.vue'
import SocialLogin from '@/views/_Accounts/components/SocialLogin.vue'
import ThemeSwitcher from '@/components/ThemeSwitcher/Index.vue'

const formName = ref('login')
const accStore = useAccount()
const router = useRouter()

const onSubmit = (payload: { email: string; password: string; redirect: string }) =>
  accStore.login(payload).then(() => {
    if (payload.redirect) router.push(payload.redirect)
    else router.push({ name: 'Home' })
  })

const toLogin = () => (formName.value = 'login')
const findPass = () => (formName.value = 'pass')

const passwordReset = (payload: { email: string }) => {
  accStore.passReset(payload)
  formName.value = 'login'
}
</script>

<template>
  <div class="bg-more-light min-vh-100 d-flex flex-row align-items-center">
    <div class="position-fixed top-0 end-0 p-3" style="z-index: 1050">
      <ThemeSwitcher size="lg" tooltip-location="bottom" />
    </div>

    <CContainer>
      <CRow class="justify-content-center">
        <CCol md="8" lg="6" xl="4">
          <CCard class="p-4 position-relative">
            <CCardBody class="text-body">
              <LoginForm
                v-if="formName === 'login'"
                @on-submit="onSubmit"
                @find-pass="findPass"
                class="mb-3"
              />

              <FindPassword
                v-else-if="formName === 'pass'"
                @on-submit="passwordReset"
                @to-login="toLogin"
              />

              <!--              <SocialLogin />-->

              <div class="mt-4 pt-3 border-top text-right">
                <span class="mr-2 small text-muted">시스템이 처음이신가요?</span>
                <a
                  href="https://docs.dyibs.com/"
                  target="_blank"
                  class="small text-decoration-none"
                >
                  사용자 매뉴얼 보기
                </a>
              </div>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>
    </CContainer>
  </div>
</template>
