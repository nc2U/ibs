<script lang="ts" setup>
import { onBeforeMount, type PropType, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MultiSelect from '@/components/MultiSelect/index.vue'

defineProps({
  allActiveProjects: {
    type: Array as PropType<{ value: string; label: string }[]>,
    default: () => [],
  },
})
const emit = defineEmits(['change-project'])

const [route, router] = [useRoute(), useRouter()]

// 검색 관련 기능 시작
const search = ref('')
const selectedProject = ref<string | null>(null)

const goSearch = () => {
  const q = search.value.trim()
  if (!q) return
  router.push({ name: '전체검색', query: { scope: '', q } })
}

const onProjectSelect = (slug: string | null) => {
  if (!slug) return
  emit('change-project', slug)
  selectedProject.value = null
}

watch(
  () => route.query.q,
  q => {
    if (typeof q === 'string') search.value = q
  },
)

onBeforeMount(() => {
  if (typeof route?.query.q === 'string') search.value = route.query.q
})
</script>

<template>
  <v-row class="align-center mb-3" no-gutters>
    <v-col cols="6" class="pa-1">
      <v-text-field
        v-model="search"
        placeholder="통합 검색 - 업무관리시스템"
        density="compact"
        variant="outlined"
        prepend-inner-icon="mdi-magnify"
        hide-details
        single-line
        class="search-input"
        @click:prepend-inner="goSearch"
        @keydown.enter="goSearch"
      />
    </v-col>
    <v-col cols="6" class="pa-1 text-body">
      <MultiSelect
        v-model="selectedProject"
        mode="single"
        :options="allActiveProjects"
        placeholder="워크스페이스 바로가기"
        @change="onProjectSelect"
      />
    </v-col>
  </v-row>
</template>

<style lang="scss" scoped>
.search-input {
  background-color: #ffffff;
}

.dark-theme .search-input {
  background-color: #41424a;
  color: #ffffff;
}
</style>
