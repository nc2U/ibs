<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import RegisterForm from './components/RegisterForm.vue'
import ThemeSwitcher from '@/components/ThemeSwitcher/Index.vue'

interface SignUser {
  email: string
  username: string
  password: string
}

const router = useRouter()
const accountStore = useAccount()
const isSubmitting = ref(false)

const onSubmit = async (payload: SignUser) => {
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    const success = await accountStore.signup(payload)
    if (success) {
      await router.replace({ name: 'Login' })
    }
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
        <CCol md="9" lg="7" xl="5">
          <CCard class="mx-4 p-4">
            <CCardBody class="text-body">
              <RegisterForm :loading="isSubmitting" @on-submit="onSubmit" />
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>
    </CContainer>
  </div>
</template>
