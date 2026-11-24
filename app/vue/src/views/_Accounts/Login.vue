<script lang="ts" setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import LoginForm from './components/LoginForm.vue'
import FindPassword from '@/views/_Accounts/components/FindPassword.vue'
import ThemeSwitcher from '@/components/ThemeSwitcher/Index.vue'

const formName = ref('login')
const isSubmitting = ref(false)
const accStore = useAccount()
const router = useRouter()

const resolveSafeRedirect = (redirect: unknown): string => {
  if (typeof redirect !== 'string') return ''
  const trimmed = redirect.trim()
  if (
    !trimmed.startsWith('/') ||
    trimmed.startsWith('//') ||
    trimmed.startsWith('/accounts/login')
  ) {
    return ''
  }
  return trimmed
}

const onSubmit = async (payload: { email: string; password: string; redirect: string }) => {
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    const user = await accStore.login(payload)
    if (user && (user.profile || user.is_superuser)) {
      const target = resolveSafeRedirect(payload.redirect)
      if (target) await router.push(target)
      else await router.push({ name: 'Home' })
    }
  } finally {
    isSubmitting.value = false
  }
}

const toLogin = () => (formName.value = 'login')
const findPass = () => (formName.value = 'pass')

const passwordReset = async (payload: { email: string }) => {
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    const ok = await accStore.passReset(payload)
    if (ok) formName.value = 'login'
  } finally {
    isSubmitting.value = false
  }
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
                :loading="isSubmitting"
                @on-submit="onSubmit"
                @find-pass="findPass"
                class="mb-3"
              />

              <FindPassword
                v-else-if="formName === 'pass'"
                :loading="isSubmitting"
                @on-submit="passwordReset"
                @to-login="toLogin"
              />

              <div class="mt-4 pt-3 border-top text-end">
                <span class="me-2 small text-muted">시스템이 처음이신가요?</span>
                <a
                  href="https://docs.dyibs.com/"
                  target="_blank"
                  rel="noopener noreferrer"
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
