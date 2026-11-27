<script setup lang="ts">
import { ref, watch, onBeforeMount, type PropType } from 'vue'
import type { Category } from '@/store/types/docs'

const props = defineProps({
  category: { type: Number, default: 0 },
  categoryList: { type: Array as PropType<Category[]>, default: () => [] },
})
const emit = defineEmits(['select-cate'])

const tab = ref(0)

watch(tab, val => {
  emit('select-cate', val)
})

watch(
  () => props.category,
  val => {
    const next = val || 0
    if (tab.value !== next) tab.value = next
  },
)

onBeforeMount(() => {
  if (props.category) tab.value = props.category
})
</script>

<template>
  <v-tabs v-model="tab" color="info" class="mt-5">
    <v-tab :value="0">전체</v-tab>
    <v-tab
      v-for="cate in categoryList"
      :key="cate.pk ?? cate.name"
      :value="cate.pk"
      :color="cate.color ?? 'info'"
    >
      {{ cate.name }}
    </v-tab>
  </v-tabs>
</template>
