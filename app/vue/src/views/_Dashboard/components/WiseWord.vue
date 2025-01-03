<script lang="ts" setup>
import { ref, computed, watch, onBeforeMount } from 'vue'
import { useStore } from '@/store'
import { useIbs } from '@/store/pinia/ibs'

const wiseWord = ref({
  pk: 0,
  saying_ko: '이또한 지나가리라.',
  saying_en: 'This too shall pass.',
  spoked_by: 'Et hoc transibit',
})

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
const wiseWordsList = computed(() => ibsStore.wiseWordsList)
const counts = computed(() => ibsStore.wiseWordsCount)

const fetchWiseWordsList = () => ibsStore.fetchWiseWordsList()

const getIndex = () => Math.floor(Math.random() * counts.value)

onBeforeMount(async () => {
  getColor()
  await fetchWiseWordsList()
  wiseWord.value = wiseWordsList.value[getIndex()]
  setInterval(() => {
    getColor()
    wiseWord.value = wiseWordsList.value[getIndex()]
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
