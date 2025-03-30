<script lang="ts" setup>
import type { PropType } from 'vue'
import type { Post } from '@/store/types/board'

defineProps({
  postList: { type: Array as PropType<Post[]>, default: () => [] },
})
</script>

<template>
  <div v-for="post in postList" :key="post.pk">
    {{ post.title }}
  </div>
</template>
