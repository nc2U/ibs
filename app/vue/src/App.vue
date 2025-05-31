<script lang="ts" setup>
import { computed, provide, watch, onMounted } from 'vue'
import { useStore } from '@/store'
import { useAccount } from '@/store/pinia/account'
import { useCompany } from '@/store/pinia/company'
import type { Company } from '@/store/types/settings.ts'

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)
const superAuth = computed(() => accStore.superAuth)
const workManager = computed(() => accStore.workManager)
provide('userInfo', userInfo)
provide('superAuth', superAuth)
provide('workManager', workManager)

const comStore = useCompany()
const company = computed<Company | null>(() => comStore.company)
provide('company', company)

const store = useStore()
const isDark = computed(() => store.theme === 'dark')
provide('isDark', isDark)
watch(isDark, () => {
  isDark.value
    ? document.body.classList.add('dark-theme')
    : document.body.classList.remove('dark-theme')
})

onMounted(() => {
  isDark.value
    ? document.body.classList.add('dark-theme')
    : document.body.classList.remove('dark-theme')
  if (accStore.isAuthorized) comStore.fetchCompany(company.value?.pk ?? comStore.initComId)
})
</script>

<template>
  <v-app>
    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>
