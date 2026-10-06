<script setup lang="ts">
import { ref, computed, watch, onBeforeMount, onBeforeUnmount } from 'vue'
import { useStore } from '@/store'
import { useIbs } from '@/store/pinia/ibs'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

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

const currentColor = ref('#9FA8DA')
let lastColorIndex = -1
let lastWordIndex = -1

const getColor = () => {
  if (colors.value.length <= 1) {
    currentColor.value = colors.value[0] || '#9FA8DA'
    return
  }
  let randomIndex = Math.floor(Math.random() * colors.value.length)
  // 직전 색상과 중복 방지
  while (randomIndex === lastColorIndex) {
    randomIndex = Math.floor(Math.random() * colors.value.length)
  }
  lastColorIndex = randomIndex
  currentColor.value = colors.value[randomIndex]
}

watch(isDark, () => getColor())

const ibsStore = useIbs()
const wiseWordsList = computed(() => ibsStore.wiseWordsList)

const fetchWiseWordsList = () => ibsStore.fetchWiseWordsList()

const getNextIndex = () => {
  const len = wiseWordsList.value.length
  if (len <= 1) return 0
  let nextIdx = Math.floor(Math.random() * len)
  // 직전 명언과 중복 방지
  while (nextIdx === lastWordIndex) {
    nextIdx = Math.floor(Math.random() * len)
  }
  lastWordIndex = nextIdx
  return nextIdx
}

const refreshWiseWord = () => {
  if (wiseWordsList.value.length > 0) {
    getColor()
    wiseWord.value = wiseWordsList.value[getNextIndex()]
  }
}

let intervalId: ReturnType<typeof setInterval> | null = null

onBeforeMount(async () => {
  getColor()
  await fetchWiseWordsList()
  if (wiseWordsList.value.length > 0) {
    wiseWord.value = wiseWordsList.value[getNextIndex()]
  }
  intervalId = setInterval(() => {
    // 탭이 백그라운드에 숨겨져 있을 때는 불필요한 렌더링 방지
    if (typeof document !== 'undefined' && document.hidden) return
    refreshWiseWord()
  }, 30000)
})

onBeforeUnmount(() => {
  if (intervalId !== null) clearInterval(intervalId)
})
</script>

<template>
  <WidgetWrapper
    :widget-id="widgetId"
    :title="title"
    :icon="icon"
    refreshable
    @refresh="refreshWiseWord"
  >
    <div class="wise-word-widget d-flex flex-column justify-center h-100">
      <v-card :color="currentColor" variant="flat" class="pa-3">
        <div class="text-body-1 font-weight-medium text-white">
          {{ wiseWord?.saying_ko ?? '' }}
        </div>
        <div class="text-caption text-white-darken-1 mt-1">
          {{ wiseWord?.saying_en ?? '' }} - {{ wiseWord?.spoked_by ?? '' }}
        </div>
      </v-card>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.wise-word-widget {
  height: 100%;
}

.text-white-darken-1 {
  color: rgba(255, 255, 255, 0.8);
}
</style>
