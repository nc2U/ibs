<script setup lang="ts">
import { ref, computed, watch, onBeforeMount } from 'vue'
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

const getColor = () => {
  const randomIndex = Math.floor(Math.random() * colors.value.length)
  currentColor.value = colors.value[randomIndex]
}

watch(isDark, () => getColor())

const ibsStore = useIbs()
const wiseWordsList = computed(() => ibsStore.wiseWordsList)
const counts = computed(() => ibsStore.wiseWordsCount)

const fetchWiseWordsList = () => ibsStore.fetchWiseWordsList()

const getIndex = () => Math.floor(Math.random() * counts.value)

const refreshWiseWord = async () => {
  if (wiseWordsList.value.length > 0) {
    getColor()
    wiseWord.value = wiseWordsList.value[getIndex()]
  }
}

onBeforeMount(async () => {
  getColor()
  await fetchWiseWordsList()
  if (wiseWordsList.value.length > 0) {
    wiseWord.value = wiseWordsList.value[getIndex()]
  }
  setInterval(() => {
    refreshWiseWord()
  }, 30000)
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
