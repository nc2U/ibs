<script lang="ts" setup>
import { ref, computed, watch, onBeforeMount } from 'vue'
import { useStore } from '@/store'
import { useIbs } from '@/store/pinia/ibs'

const store = useStore()
const isDark = computed(() => store.theme === 'dark')

const colors = ref([
  '#E57373',
  '#F06292',
  '#CE93D8',
  '#B39DDB',
  '#9FA8DA',
  '#42A5F5',
  '#039BE5',
  '#00ACC1',
  '#4DB6AC',
  '#66BB6A',
  '#7CB342',
  '#9E9D24',
  '#F57F17',
  '#FF7043',
  '#A1887F',
  '#90A4AE',
  '#757575',
])

const getColor = () => {
  const randomIndex = Math.floor(Math.random() * colors.value.length)
  defaults.value.VCard.color = colors.value[randomIndex]
}

const defaults = ref({
  global: {
    elevation: 5,
  },
  VCard: {
    color: '#9FA8DA',
  },
})

watch(isDark, nVal => getColor())

const ibsStore = useIbs()
const wiseWord = computed(() => ibsStore.wiseWord)
const wiseWordsCount = computed(() => ibsStore.wiseWordsCount)

const fetchWiseWordsList = () => ibsStore.fetchWiseWordsList()
const fetchWiseWord = (pk: number) => ibsStore.fetchWiseWord(pk)

const getPk = (max: number) => Math.floor(Math.random() * (max - 1) + 1)

onBeforeMount(async () => {
  getColor()
  await fetchWiseWordsList()
  await fetchWiseWord(getPk(wiseWordsCount.value + 1))
  setInterval(() => {
    getColor()
    fetchWiseWord(getPk(wiseWordsCount.value + 1))
  }, 30000)
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
