<script lang="ts" setup>
import { computed, onMounted, watch } from 'vue'
import { useStore } from '@/store'
import { useCompany } from '@/store/pinia/company'
import GlobalDownloadIndicator from '@/components/DownLoad/GlobalDownloadIndicator.vue'

const comStore = useCompany()
const company = computed(() => comStore.company)

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
