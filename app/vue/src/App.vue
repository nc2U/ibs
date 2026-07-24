<script lang="ts" setup>
import { computed, onMounted, watch } from 'vue'
import { useStore } from '@/store'
import { useCompany } from '@/store/pinia/company'
import { useWork } from '@/store/pinia/work_project'
import { useAccount } from '@/store/pinia/account'
import GlobalDownloadIndicator from '@/components/DownLoad/GlobalDownloadIndicator.vue'

const comStore = useCompany()
const company = computed(() => comStore.company)

const workStore = useWork()
const accountStore = useAccount()

const store = useStore()
const isDark = computed(() => store.theme === 'dark')

watch(isDark, () => {
  isDark.value
    ? document.body.classList.add('dark-theme')
    : document.body.classList.remove('dark-theme')
})

onMounted(async () => {
  isDark.value
    ? document.body.classList.add('dark-theme')
    : document.body.classList.remove('dark-theme')
  if (!company.value) await comStore.fetchCompany(comStore.initComId)
  
  // 로그인된 경우 전역에서 사용할 수 있게 참여 프로젝트 리스트 로딩
  if (accountStore.userInfo) {
    await workStore.fetchMyProjectsList()
  }
})
</script>

<template>
  <v-app>
    <v-main>
      <router-view />
    </v-main>

    <!-- 글로벌 다운로드 인디케이터 -->
    <GlobalDownloadIndicator />
  </v-app>
</template>
