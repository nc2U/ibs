<script lang="ts" setup>
import { ref, computed, watch, onBeforeMount } from 'vue'
import { useStore } from '@/store'
import { useIbs } from '@/store/pinia/ibs'

const store = useStore()
const isDark = computed(() => store.theme === 'dark')

const bgColor = computed(() => (isDark.value ? 'success' : 'light'))

const defaults = ref({
  global: {
    elevation: 5,
  },
  VCard: {
    color: bgColor.value,
  },
})

watch(isDark, nVal => {
  defaults.value.VCard.color = nVal ? 'success' : 'light'
})

const ibsStore = useIbs()
const wiseWord = computed(() => ibsStore.wiseWord)
const wiseWordsCount = computed(() => ibsStore.wiseWordsCount)

const fetchWiseWordsList = () => ibsStore.fetchWiseWordsList()
const fetchWiseWord = (pk: number) => ibsStore.fetchWiseWord(pk)

const getPk = (max: number) => Math.floor(Math.random() * (max - 1) + 1)

onBeforeMount(async () => {
  await fetchWiseWordsList()
  await fetchWiseWord(getPk(wiseWordsCount.value + 1))
  setInterval(() => {
    fetchWiseWord(getPk(wiseWordsCount.value + 1))
  }, 90000)
})
</script>

<template>
  <v-defaults-provider :defaults="defaults">
    <v-card
      :title="wiseWord?.saying_ko ?? ''"
      :subtitle="`${wiseWord?.saying_en ?? ''} - ${wiseWord?.spoked_by ?? ''}`"
      class="mb-4"
    />
  </v-defaults-provider>
</template>
