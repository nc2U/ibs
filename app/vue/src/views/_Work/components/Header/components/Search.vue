<script lang="ts" setup>
import { onBeforeMount, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MultiSelect from '@/components/MultiSelect/index.vue'

defineProps({ allActiveProjects: { type: Array, default: () => [] } })
const emit = defineEmits(['change-project'])

const [route, router] = [useRoute(), useRouter()]

// 검색 관련 기능 시작
const search = ref('')
const goSearch = () => router.push({ name: '전체검색', query: { scope: '', q: search.value } })

onBeforeMount(async () => {
  if (route?.query.q) search.value = route.query.q as string
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
        @focus="search = ''"
      />
    </v-col>
    <v-col cols="6" class="pa-1 text-body">
      <MultiSelect
        mode="single"
        :options="allActiveProjects"
        placeholder="프로젝트 바로가기"
        @change="emit('change-project', $event)"
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
